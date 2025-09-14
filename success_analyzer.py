#!/usr/bin/env python3
"""
🎯 SUCCESS RATE ANALYZER - Herramienta simple para analizar success rate
- Sube CSV con dominios
- Ve success rate en tiempo real
- Analiza qué falla y por qué
"""

import asyncio
import time
import csv
import json
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import threading
from collections import Counter

sys.path.append('/workspaces/gtm-scaner')

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient
from app.main import app as scanner_app
import uvicorn

class SuccessAnalyzer:
    def __init__(self):
        self.app = FastAPI(title="GTM Scanner - Success Rate Analyzer")
        self.scanner_client = TestClient(scanner_app)
        self.current_analysis = None
        
        self.setup_routes()
    
    def setup_routes(self):
        """Configura las rutas de la app"""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            return self.get_dashboard_html()
        
        @self.app.post("/analyze")
        async def analyze_csv(file: UploadFile = File(...)):
            """Analiza un CSV con dominios"""
            try:
                # Validar archivo CSV
                if not file.filename.endswith('.csv'):
                    raise HTTPException(400, "Solo archivos CSV permitidos")
                
                # Leer contenido
                content = await file.read()
                csv_content = content.decode('utf-8')
                
                # Parsear CSV
                domains = self.parse_csv(csv_content)
                
                if not domains:
                    raise HTTPException(400, "No se encontraron dominios válidos en el CSV")
                
                # Analizar dominios
                analysis_result = await self.analyze_domains(domains)
                
                # Guardar resultado actual
                self.current_analysis = analysis_result
                
                return analysis_result
                
            except Exception as e:
                raise HTTPException(400, f"Error procesando archivo: {str(e)}")
    
    def parse_csv(self, content: str) -> List[str]:
        """Extrae dominios del CSV"""
        domains = []
        
        # Intentar leer como CSV
        lines = content.strip().split('\n')
        
        # Si es una sola columna sin header
        if len(lines) > 0 and ',' not in lines[0]:
            domains = [line.strip() for line in lines if line.strip()]
        else:
            # CSV con columnas
            reader = csv.DictReader(lines)
            
            # Buscar columna con dominios
            domain_columns = ['domain', 'domains', 'website', 'url', 'site']
            
            for row in reader:
                domain_found = False
                for col_name in domain_columns:
                    for key in row.keys():
                        if col_name.lower() in key.lower():
                            domain = row[key].strip()
                            if domain:
                                domains.append(domain)
                                domain_found = True
                                break
                    if domain_found:
                        break
                
                # Si no encuentra columna específica, usar primera columna
                if not domain_found and row:
                    first_value = list(row.values())[0].strip()
                    if first_value:
                        domains.append(first_value)
        
        # Limpiar dominios
        clean_domains = []
        for domain in domains:
            # Remover protocolo si existe
            if domain.startswith(('http://', 'https://')):
                domain = domain.split('://', 1)[1]
            
            # Remover www. si existe
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Remover path si existe
            if '/' in domain:
                domain = domain.split('/')[0]
            
            # Validar que parece un dominio
            if '.' in domain and len(domain) > 3:
                clean_domains.append(domain)
        
        return list(set(clean_domains))  # Remover duplicados
    
    async def analyze_domains(self, domains: List[str]) -> Dict:
        """Analiza una lista de dominios"""
        print(f"\n🎯 Analizando {len(domains)} dominios...")
        
        results = {
            'total_domains': len(domains),
            'successful': [],
            'failed': [],
            'start_time': time.time(),
            'domains_tested': domains
        }
        
        # Analizar en paralelo (pero limitado para no sobrecargar)
        max_workers = 3
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Crear tareas
            future_to_domain = {
                executor.submit(self.test_domain, domain): domain 
                for domain in domains
            }
            
            # Procesar resultados
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    result = future.result()
                    
                    if result['success']:
                        results['successful'].append(result)
                        print(f"✅ {domain}")
                    else:
                        results['failed'].append(result)
                        print(f"❌ {domain} - {result['error']}")
                        
                except Exception as e:
                    results['failed'].append({
                        'domain': domain,
                        'success': False,
                        'error': f"Exception: {str(e)}",
                        'scan_time': 0
                    })
                    print(f"💥 {domain} - Exception: {str(e)}")
        
        # Calcular métricas finales
        results['end_time'] = time.time()
        results['total_time'] = results['end_time'] - results['start_time']
        results['success_rate'] = len(results['successful']) / len(domains) * 100
        
        # Análisis profundo de datos
        all_results = results['successful'] + results['failed']
        results['analysis'] = {
            'failures': self.analyze_failures(results['failed']),
            'companies': self.analyze_companies(results['successful']),
            'industries': self.analyze_industries(results['successful']),
            'performance': self.analyze_performance(all_results)
        }
        
        print(f"\n📊 Análisis completado:")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Exitosos: {len(results['successful'])}")
        print(f"   Fallidos: {len(results['failed'])}")
        print(f"   Tiempo total: {results['total_time']:.1f}s")
        
        return results
    
    def test_domain(self, domain: str) -> Dict:
        """Testea un dominio individual"""
        start_time = time.time()
        
        try:
            # Hacer request al scanner
            response = self.scanner_client.post('/scan', json={
                'domain': domain,
                'max_pages': 1,
                'respect_robots': False
            })
            
            scan_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'domain': domain,
                    'success': True,
                    'scan_time': scan_time,
                    'company_name': data.get('company_name'),
                    'industry': data.get('industry'),
                    'tech_count': len(data.get('tech_stack', {})),
                    'social_count': len(data.get('social', {})),
                    'has_enrichment': bool(data.get('enrichment')),
                    'raw_data': data  # Guardar datos completos para análisis profundo
                }
            else:
                return {
                    'domain': domain,
                    'success': False,
                    'scan_time': scan_time,
                    'error': f"HTTP {response.status_code}",
                    'response_text': response.text[:200] if response.text else ""
                }
                
        except Exception as e:
            return {
                'domain': domain,
                'success': False,
                'scan_time': time.time() - start_time,
                'error': str(e)
            }
    
    def analyze_failures(self, failed_results: List[Dict]) -> Dict:
        """Analiza los fallos para encontrar patrones"""
        if not failed_results:
            return {}
        
        # Contar tipos de errores
        error_types = Counter()
        slow_domains = []
        
        for result in failed_results:
            error = result.get('error', 'Unknown')
            
            # Categorizar errores
            if 'timeout' in error.lower() or 'timed out' in error.lower():
                error_types['Timeout'] += 1
            elif '404' in error or 'Not Found' in error:
                error_types['404 Not Found'] += 1
            elif '403' in error or 'Forbidden' in error:
                error_types['403 Forbidden'] += 1
            elif '500' in error or 'Internal Server' in error:
                error_types['500 Server Error'] += 1
            elif 'connection' in error.lower():
                error_types['Connection Error'] += 1
            elif 'ssl' in error.lower() or 'certificate' in error.lower():
                error_types['SSL/Certificate Error'] += 1
            else:
                error_types['Other'] += 1
            
            # Identificar dominios lentos
            if result.get('scan_time', 0) > 10:
                slow_domains.append(result['domain'])
        
        # Dominios más problemáticos
        problem_tlds = Counter()
        for result in failed_results:
            domain = result['domain']
            if '.' in domain:
                tld = domain.split('.')[-1]
                problem_tlds[tld] += 1
        
        return {
            'error_types': dict(error_types.most_common()),
            'slow_domains': slow_domains,
            'problem_tlds': dict(problem_tlds.most_common(5)),
            'total_failed': len(failed_results),
            'avg_fail_time': sum(r.get('scan_time', 0) for r in failed_results) / len(failed_results)
        }
    
    def analyze_companies(self, successful_results: List[Dict]) -> Dict:
        """Análisis profundo de datos de empresas"""
        if not successful_results:
            return {}
        
        # Estadísticas básicas
        total = len(successful_results)
        with_names = len([r for r in successful_results if r.get('company_name')])
        with_enrichment = len([r for r in successful_results if r.get('has_enrichment')])
        
        # Análisis de tecnologías
        tech_counts = [r.get('tech_count', 0) for r in successful_results]
        avg_tech = sum(tech_counts) / len(tech_counts) if tech_counts else 0
        max_tech = max(tech_counts) if tech_counts else 0
        
        # Análisis de redes sociales
        social_counts = [r.get('social_count', 0) for r in successful_results]
        avg_social = sum(social_counts) / len(social_counts) if social_counts else 0
        
        # Top empresas por tecnologías
        top_tech_companies = sorted(successful_results, key=lambda x: x.get('tech_count', 0), reverse=True)[:10]
        
        # Distribución de tiempos de scan
        scan_times = [r.get('scan_time', 0) for r in successful_results]
        avg_scan_time = sum(scan_times) / len(scan_times) if scan_times else 0
        
        return {
            'total_companies': total,
            'name_extraction_rate': (with_names / total) * 100,
            'enrichment_rate': (with_enrichment / total) * 100,
            'avg_technologies': avg_tech,
            'max_technologies': max_tech,
            'avg_social_media': avg_social,
            'avg_scan_time': avg_scan_time,
            'top_tech_companies': [
                {
                    'domain': comp['domain'],
                    'company_name': comp.get('company_name', 'N/A'),
                    'tech_count': comp.get('tech_count', 0)
                } for comp in top_tech_companies
            ],
            'tech_distribution': {
                '0 tech': len([r for r in successful_results if r.get('tech_count', 0) == 0]),
                '1-5 tech': len([r for r in successful_results if 1 <= r.get('tech_count', 0) <= 5]),
                '6-10 tech': len([r for r in successful_results if 6 <= r.get('tech_count', 0) <= 10]),
                '11+ tech': len([r for r in successful_results if r.get('tech_count', 0) > 10])
            }
        }
    
    def analyze_industries(self, successful_results: List[Dict]) -> Dict:
        """Análisis de distribución de industrias"""
        if not successful_results:
            return {}
        
        # Extraer industrias de los resultados
        industries = []
        for result in successful_results:
            # Buscar industry en los datos raw si está disponible
            if 'raw_data' in result and result['raw_data']:
                industry = result['raw_data'].get('industry')
                if industry and industry != 'None':
                    industries.append(industry)
        
        if not industries:
            return {'message': 'No industry data available'}
        
        # Contar industrias
        industry_counts = Counter(industries)
        total_with_industry = len(industries)
        
        # Calcular distribución
        industry_distribution = {}
        for industry, count in industry_counts.most_common():
            percentage = (count / total_with_industry) * 100
            industry_distribution[industry] = {
                'count': count,
                'percentage': percentage
            }
        
        return {
            'total_with_industry': total_with_industry,
            'industry_detection_rate': (total_with_industry / len(successful_results)) * 100,
            'top_industries': dict(industry_counts.most_common(10)),
            'industry_distribution': industry_distribution
        }
    
    def analyze_performance(self, all_results: List[Dict]) -> Dict:
        """Análisis de performance del scanner"""
        if not all_results:
            return {}
        
        scan_times = [r.get('scan_time', 0) for r in all_results]
        successful_times = [r.get('scan_time', 0) for r in all_results if r.get('success')]
        failed_times = [r.get('scan_time', 0) for r in all_results if not r.get('success')]
        
        # Estadísticas generales
        avg_time = sum(scan_times) / len(scan_times) if scan_times else 0
        min_time = min(scan_times) if scan_times else 0
        max_time = max(scan_times) if scan_times else 0
        
        # Performance por status
        avg_success_time = sum(successful_times) / len(successful_times) if successful_times else 0
        avg_failed_time = sum(failed_times) / len(failed_times) if failed_times else 0
        
        # Distribución de tiempos
        time_distribution = {
            'Fast (0-2s)': len([t for t in scan_times if 0 <= t <= 2]),
            'Medium (2-5s)': len([t for t in scan_times if 2 < t <= 5]),
            'Slow (5-10s)': len([t for t in scan_times if 5 < t <= 10]),
            'Very Slow (10s+)': len([t for t in scan_times if t > 10])
        }
        
        # Encontrar extremos
        fastest_scan = min(all_results, key=lambda x: x.get('scan_time', float('inf')))
        slowest_scan = max(all_results, key=lambda x: x.get('scan_time', 0))
        
        return {
            'avg_scan_time': avg_time,
            'min_scan_time': min_time,
            'max_scan_time': max_time,
            'avg_success_time': avg_success_time,
            'avg_failed_time': avg_failed_time,
            'time_distribution': time_distribution,
            'fastest_domain': {
                'domain': fastest_scan.get('domain'),
                'time': fastest_scan.get('scan_time', 0)
            },
            'slowest_domain': {
                'domain': slowest_scan.get('domain'),
                'time': slowest_scan.get('scan_time', 0)
            },
            'performance_insights': self.get_performance_insights(avg_time, time_distribution)
        }
    
    def get_performance_insights(self, avg_time: float, time_dist: Dict) -> List[str]:
        """Genera insights de performance"""
        insights = []
        
        if avg_time < 2:
            insights.append("🚀 Excelente performance promedio")
        elif avg_time < 5:
            insights.append("✅ Performance aceptable")
        else:
            insights.append("⚠️ Performance puede mejorarse")
        
        slow_percentage = (time_dist.get('Slow (5-10s)', 0) + time_dist.get('Very Slow (10s+)', 0)) / sum(time_dist.values()) * 100
        if slow_percentage > 30:
            insights.append(f"🐌 {slow_percentage:.1f}% de scans son lentos")
        
        fast_percentage = time_dist.get('Fast (0-2s)', 0) / sum(time_dist.values()) * 100
        if fast_percentage > 70:
            insights.append(f"⚡ {fast_percentage:.1f}% de scans son rápidos")
        
        return insights
    
    def get_dashboard_html(self) -> str:
        """HTML del dashboard simple"""
        return """
<!DOCTYPE html>
<html>
<head>
    <title>GTM Scanner - Success Rate Analyzer</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { 
            font-family: 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f7fa; 
        }
        .container { 
            max-width: 1000px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 40px 30px; 
            text-align: center; 
        }
        .header h1 { margin: 0; font-size: 2.2em; font-weight: 300; }
        .header p { margin: 10px 0 0 0; opacity: 0.9; font-size: 1.1em; }
        
        .section { padding: 30px; border-bottom: 1px solid #eee; }
        .section:last-child { border-bottom: none; }
        .section h2 { 
            margin-top: 0; 
            color: #333; 
            font-weight: 500;
            border-bottom: 2px solid #667eea; 
            padding-bottom: 10px; 
        }
        
        .upload-zone {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 50px 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            background: #fafbff;
        }
        .upload-zone:hover { 
            border-color: #764ba2; 
            background: #f0f2ff; 
            transform: translateY(-2px);
        }
        .upload-zone.dragover { 
            border-color: #4caf50; 
            background: #f0f8f0; 
        }
        
        .upload-icon { 
            font-size: 3em; 
            color: #667eea; 
            margin-bottom: 20px; 
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: all 0.3s ease;
            margin: 10px;
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); 
        }
        
        .results-section { display: none; }
        
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .metric-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }
        .metric-card:hover { transform: translateY(-5px); }
        .metric-value { 
            font-size: 2.5em; 
            font-weight: bold; 
            color: #667eea; 
            margin-bottom: 5px;
        }
        .metric-label { 
            color: #666; 
            font-weight: 500;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }
        
        .success-rate {
            font-size: 4em !important;
            background: linear-gradient(135deg, #4caf50, #8bc34a);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 30px 0;
            background: #fafafa;
            border-radius: 12px;
            padding: 20px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            margin: 20px 0;
            overflow: hidden;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4caf50, #8bc34a);
            width: 0%;
            transition: width 0.5s ease;
        }
        
        .analysis-section {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
        }
        
        .error-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .error-item {
            background: white;
            border-left: 4px solid #f44336;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        .error-type { font-weight: bold; color: #f44336; }
        .error-count { font-size: 1.5em; color: #666; }
        
        .domain-list {
            background: white;
            border-radius: 8px;
            max-height: 200px;
            overflow-y: auto;
            padding: 15px;
            border: 1px solid #ddd;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            display: none;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .analysis-tabs {
            display: flex;
            border-bottom: 2px solid #eee;
            margin-bottom: 30px;
        }
        .tab-btn {
            background: none;
            border: none;
            padding: 15px 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }
        .tab-btn:hover { color: #667eea; }
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
            background: #f8f9ff;
        }
        
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        
        .breakdown-section {
            background: #f8f9fa;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
        }
        
        .top-list {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
        }
        .list-item:last-child { border-bottom: none; }
        
        .item-name { font-weight: 500; color: #333; }
        .item-value { color: #667eea; font-weight: bold; }
        .item-bar {
            flex: 1;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            margin: 0 15px;
            overflow: hidden;
        }
        .item-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
        }
        
        .alert {
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            font-weight: 500;
        }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        
        .sample-format {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            border-left: 4px solid #667eea;
        }
        
        /* Estilos para pestañas de análisis */
        .analysis-tabs {
            display: flex;
            border-bottom: 2px solid #e0e0e0;
            margin-bottom: 30px;
            overflow-x: auto;
        }
        .tab-btn {
            background: none;
            border: none;
            padding: 15px 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        .tab-btn:hover {
            color: #667eea;
            background: #f8f9ff;
        }
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        
        .breakdown-section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .top-list {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        .top-list h3 {
            margin-top: 0;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .list-item {
            display: flex;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid #f0f0f0;
        }
        .list-item:last-child {
            border-bottom: none;
        }
        .list-rank {
            font-weight: bold;
            color: #667eea;
            width: 30px;
        }
        .list-name {
            flex: 1;
            font-weight: 500;
            color: #333;
        }
        .list-value {
            color: #667eea;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .insight-box {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
            border: 1px solid #4caf50;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }
        .insight-box h4 {
            margin-top: 0;
            color: #2e7d32;
        }
        .insight-item {
            padding: 8px 0;
            color: #2e7d32;
            font-weight: 500;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Success Rate Analyzer</h1>
            <p>Sube un CSV con dominios y analiza el success rate del GTM Scanner</p>
        </div>
        
        <div class="section">
            <h2>📁 Subir archivo CSV</h2>
            <div class="upload-zone" id="uploadZone">
                <div class="upload-icon">📊</div>
                <h3>Arrastra tu CSV aquí o haz click para seleccionar</h3>
                <p>El archivo debe contener dominios (una columna llamada "domain" o similar)</p>
                <input type="file" id="fileInput" accept=".csv" style="display: none;">
            </div>
            
            <div class="sample-format">
                <strong>📋 Formato esperado:</strong><br>
                domain<br>
                google.com<br>
                microsoft.com<br>
                amazon.com<br><br>
                <em>O simplemente una lista de dominios, uno por línea</em>
            </div>
        </div>
        
        <div class="loading" id="loadingSection">
            <div class="spinner"></div>
            <h3>Analizando dominios...</h3>
            <p>Esto puede tomar unos minutos dependiendo del número de dominios</p>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div id="progressText">Preparando análisis...</div>
        </div>
        
        <div class="section results-section" id="resultsSection">
            <h2>📊 Resultados del Análisis</h2>
            
            <div class="metrics-grid" id="metricsGrid">
                <!-- Métricas se llenan dinámicamente -->
            </div>
            
            <div class="chart-container">
                <canvas id="resultsChart"></canvas>
            </div>
        </div>
        
        <div class="section results-section" id="dataAnalysisSection">
            <h2>🔍 Análisis Profundo de Datos</h2>
            
            <div class="analysis-tabs">
                <button class="tab-btn active" onclick="switchTab('companies')">🏢 Empresas</button>
                <button class="tab-btn" onclick="switchTab('industries')">🏭 Industrias</button>
                <button class="tab-btn" onclick="switchTab('technologies')">💻 Tecnologías</button>
                <button class="tab-btn" onclick="switchTab('performance')">⚡ Performance</button>
            </div>
            
            <div id="companiesTab" class="tab-content active">
                <div class="metrics-grid" id="companyMetrics"></div>
                <div class="chart-container">
                    <canvas id="companyChart"></canvas>
                </div>
                <div id="topCompanies" class="top-list"></div>
            </div>
            
            <div id="industriesTab" class="tab-content">
                <div class="chart-container">
                    <canvas id="industryChart"></canvas>
                </div>
                <div id="industryBreakdown" class="breakdown-section"></div>
            </div>
            
            <div id="technologiesTab" class="tab-content">
                <div class="chart-container">
                    <canvas id="techChart"></canvas>
                </div>
                <div id="techBreakdown" class="breakdown-section"></div>
            </div>
            
            <div id="performanceTab" class="tab-content">
                <div class="metrics-grid" id="performanceMetrics"></div>
                <div class="chart-container">
                    <canvas id="performanceChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="section results-section" id="analysisSection">
            <h2>🔍 Análisis de Fallos</h2>
            <div class="analysis-section">
                <h3>Tipos de errores encontrados:</h3>
                <div class="error-list" id="errorsList">
                    <!-- Errores se llenan dinámicamente -->
                </div>
                
                <div id="failedDomainsSection" style="margin-top: 30px;">
                    <h3>Dominios que fallaron:</h3>
                    <div class="domain-list" id="failedDomainsList">
                        <!-- Lista de dominios fallidos -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let analysisInProgress = false;
        
        // File upload handling
        document.getElementById('uploadZone').addEventListener('click', () => {
            document.getElementById('fileInput').click();
        });
        
        document.getElementById('fileInput').addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                analyzeFile(e.target.files[0]);
            }
        });
        
        // Drag and drop
        const uploadZone = document.getElementById('uploadZone');
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                analyzeFile(e.dataTransfer.files[0]);
            }
        });
        
        async function analyzeFile(file) {
            if (analysisInProgress) {
                alert('Ya hay un análisis en progreso');
                return;
            }
            
            if (!file.name.endsWith('.csv')) {
                showAlert('Solo se permiten archivos CSV', 'error');
                return;
            }
            
            analysisInProgress = true;
            showLoading();
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Error ${response.status}: ${await response.text()}`);
                }
                
                const results = await response.json();
                showResults(results);
                
            } catch (error) {
                showAlert(`Error analizando archivo: ${error.message}`, 'error');
                hideLoading();
            }
            
            analysisInProgress = false;
        }
        
        function showLoading() {
            document.getElementById('loadingSection').style.display = 'block';
            document.querySelectorAll('.results-section').forEach(section => {
                section.style.display = 'none';
            });
        }
        
        function hideLoading() {
            document.getElementById('loadingSection').style.display = 'none';
        }
        
        function showResults(results) {
            hideLoading();
            
            // Mostrar secciones de resultados
            document.querySelectorAll('.results-section').forEach(section => {
                section.style.display = 'block';
            });
            
            // Llenar métricas principales
            const metricsHtml = `
                <div class="metric-card">
                    <div class="metric-value success-rate">${results.success_rate.toFixed(1)}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${results.successful.length}</div>
                    <div class="metric-label">Exitosos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${results.failed.length}</div>
                    <div class="metric-label">Fallidos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${results.total_domains}</div>
                    <div class="metric-label">Total Dominios</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${results.total_time.toFixed(1)}s</div>
                    <div class="metric-label">Tiempo Total</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${(results.total_domains / results.total_time).toFixed(1)}/s</div>
                    <div class="metric-label">Velocidad</div>
                </div>
            `;
            document.getElementById('metricsGrid').innerHTML = metricsHtml;
            
            // Crear gráfico principal
            createChart(results);
            
            // Mostrar análisis profundo
            showDeepAnalysis(results);
            
            // Mostrar análisis de fallos
            showFailureAnalysis(results.analysis.failures, results.failed);
            
            showAlert(`Análisis completado: ${results.success_rate.toFixed(1)}% success rate`, 'success');
        }
        
        function createChart(results) {
            const ctx = document.getElementById('resultsChart').getContext('2d');
            
            // Datos para el gráfico
            const chartData = {
                labels: ['Exitosos', 'Fallidos'],
                datasets: [{
                    data: [results.successful.length, results.failed.length],
                    backgroundColor: ['#4caf50', '#f44336'],
                    borderWidth: 0,
                    hoverOffset: 10
                }]
            };
            
            new Chart(ctx, {
                type: 'doughnut',
                data: chartData,
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: { size: 14 }
                            }
                        },
                        title: {
                            display: true,
                            text: 'Distribución de Resultados',
                            font: { size: 18, weight: 'bold' },
                            padding: 20
                        }
                    }
                }
            });
        }
        
        function showDataAnalysis(results) {
            document.getElementById('dataAnalysisSection').style.display = 'block';
            
            // Analizar datos de empresas exitosas
            const successfulData = results.successful;
            
            // Análisis de empresas
            showCompanyAnalysis(successfulData);
            
            // Análisis de industrias
            showIndustryAnalysis(successfulData);
            
            // Análisis de tecnologías
            showTechnologyAnalysis(successfulData);
            
            // Análisis de performance
            showPerformanceAnalysis(results);
        }
        
        function showCompanyAnalysis(data) {
            // Métricas de empresas
            const withNames = data.filter(d => d.company_name && d.company_name !== 'None').length;
            const withEnrichment = data.filter(d => d.has_enrichment).length;
            const avgTech = data.reduce((sum, d) => sum + d.tech_count, 0) / data.length;
            const avgSocial = data.reduce((sum, d) => sum + d.social_count, 0) / data.length;
            
            const companyMetricsHtml = `
                <div class="metric-card">
                    <div class="metric-value">${((withNames / data.length) * 100).toFixed(1)}%</div>
                    <div class="metric-label">Nombres Extraídos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${((withEnrichment / data.length) * 100).toFixed(1)}%</div>
                    <div class="metric-label">Con Enrichment</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${avgTech.toFixed(1)}</div>
                    <div class="metric-label">Avg Tech Stack</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${avgSocial.toFixed(1)}</div>
                    <div class="metric-label">Avg Social Media</div>
                </div>
            `;
            document.getElementById('companyMetrics').innerHTML = companyMetricsHtml;
            
            // Chart de distribución de tech stack
            const techDistribution = {};
            data.forEach(d => {
                const count = d.tech_count;
                const key = count === 0 ? '0' : count <= 2 ? '1-2' : count <= 5 ? '3-5' : count <= 10 ? '6-10' : '10+';
                techDistribution[key] = (techDistribution[key] || 0) + 1;
            });
            
            const ctx = document.getElementById('companyChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(techDistribution),
                    datasets: [{
                        label: 'Empresas',
                        data: Object.values(techDistribution),
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución de Tecnologías por Empresa'
                        }
                    }
                }
            });
            
            // Top empresas por tech stack
            const topCompanies = data
                .filter(d => d.company_name && d.company_name !== 'None')
                .sort((a, b) => b.tech_count - a.tech_count)
                .slice(0, 10);
            
            let topCompaniesHtml = '<h3>🏆 Top Empresas por Tech Stack</h3>';
            topCompanies.forEach((company, index) => {
                const percentage = (company.tech_count / Math.max(...data.map(d => d.tech_count))) * 100;
                topCompaniesHtml += `
                    <div class="list-item">
                        <span class="item-name">${company.company_name}</span>
                        <div class="item-bar">
                            <div class="item-fill" style="width: ${percentage}%"></div>
                        </div>
                        <span class="item-value">${company.tech_count} techs</span>
                    </div>
                `;
            });
            document.getElementById('topCompanies').innerHTML = topCompaniesHtml;
        }
        
        function showIndustryAnalysis(data) {
            // Contar industrias
            const industries = {};
            data.forEach(d => {
                if (d.industry && d.industry !== 'None') {
                    industries[d.industry] = (industries[d.industry] || 0) + 1;
                }
            });
            
            // Chart de industrias
            const ctx = document.getElementById('industryChart').getContext('2d');
            const industryEntries = Object.entries(industries).sort((a, b) => b[1] - a[1]).slice(0, 10);
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: industryEntries.map(([name]) => name),
                    datasets: [{
                        data: industryEntries.map(([, count]) => count),
                        backgroundColor: [
                            '#667eea', '#764ba2', '#4caf50', '#f44336', '#ff9800',
                            '#9c27b0', '#2196f3', '#00bcd4', '#8bc34a', '#ffeb3b'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución por Industrias'
                        }
                    }
                }
            });
            
            // Breakdown de industrias
            let industryHtml = '<h3>📊 Breakdown de Industrias</h3>';
            industryEntries.forEach(([industry, count]) => {
                const percentage = (count / data.length) * 100;
                industryHtml += `
                    <div class="list-item">
                        <span class="item-name">${industry}</span>
                        <div class="item-bar">
                            <div class="item-fill" style="width: ${(count / industryEntries[0][1]) * 100}%"></div>
                        </div>
                        <span class="item-value">${count} (${percentage.toFixed(1)}%)</span>
                    </div>
                `;
            });
            document.getElementById('industryBreakdown').innerHTML = industryHtml;
        }
        
        function showTechnologyAnalysis(data) {
            // Analizar tecnologías (esto requiere más datos del backend)
            const ctx = document.getElementById('techChart').getContext('2d');
            
            // Por ahora, mostrar distribución de tech count
            const techCounts = data.map(d => d.tech_count);
            const avgTech = techCounts.reduce((a, b) => a + b, 0) / techCounts.length;
            const maxTech = Math.max(...techCounts);
            const minTech = Math.min(...techCounts);
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.map((_, i) => `Empresa ${i + 1}`),
                    datasets: [{
                        label: 'Tecnologías Detectadas',
                        data: techCounts,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Evolución de Detección de Tecnologías'
                        }
                    }
                }
            });
            
            let techHtml = `
                <h3>💻 Estadísticas de Tecnologías</h3>
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-value">${avgTech.toFixed(1)}</div>
                        <div class="metric-label">Promedio</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${maxTech}</div>
                        <div class="metric-label">Máximo</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${minTech}</div>
                        <div class="metric-label">Mínimo</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${((data.filter(d => d.tech_count > 0).length / data.length) * 100).toFixed(1)}%</div>
                        <div class="metric-label">Con Tecnologías</div>
                    </div>
                </div>
            `;
            document.getElementById('techBreakdown').innerHTML = techHtml;
        }
        
        function showPerformanceAnalysis(results) {
            const successful = results.successful;
            const failed = results.failed;
            
            // Métricas de performance
            const avgScanTime = successful.reduce((sum, d) => sum + d.scan_time, 0) / successful.length;
            const fastestScan = Math.min(...successful.map(d => d.scan_time));
            const slowestScan = Math.max(...successful.map(d => d.scan_time));
            const throughput = results.total_domains / results.total_time;
            
            const performanceMetricsHtml = `
                <div class="metric-card">
                    <div class="metric-value">${avgScanTime.toFixed(2)}s</div>
                    <div class="metric-label">Tiempo Promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${fastestScan.toFixed(2)}s</div>
                    <div class="metric-label">Más Rápido</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${slowestScan.toFixed(2)}s</div>
                    <div class="metric-label">Más Lento</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${throughput.toFixed(1)}/s</div>
                    <div class="metric-label">Throughput</div>
                </div>
            `;
            document.getElementById('performanceMetrics').innerHTML = performanceMetricsHtml;
            
            // Chart de tiempos de scan
            const ctx = document.getElementById('performanceChart').getContext('2d');
            const scanTimes = successful.map(d => d.scan_time);
            
            new Chart(ctx, {
                type: 'histogram',
                data: {
                    labels: Array.from({length: 20}, (_, i) => `${i * 0.5}-${(i + 1) * 0.5}s`),
                    datasets: [{
                        label: 'Distribución de Tiempos',
                        data: Array.from({length: 20}, (_, i) => {
                            const min = i * 0.5;
                            const max = (i + 1) * 0.5;
                            return scanTimes.filter(t => t >= min && t < max).length;
                        }),
                        backgroundColor: 'rgba(102, 126, 234, 0.8)'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución de Tiempos de Scan'
                        }
                    }
                }
            });
        }
        
        function switchTab(tabName) {
            // Ocultar todas las tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Mostrar tab seleccionada
            document.getElementById(tabName + 'Tab').classList.add('active');
            event.target.classList.add('active');
        }
        
        function showFailureAnalysis(analysis, failedResults) {
            if (!analysis || !analysis.error_types) {
                document.getElementById('analysisSection').style.display = 'none';
                return;
            }
            
            // Mostrar tipos de errores
            let errorsHtml = '';
            for (const [errorType, count] of Object.entries(analysis.error_types)) {
                errorsHtml += `
                    <div class="error-item">
                        <div class="error-type">${errorType}</div>
                        <div class="error-count">${count} dominios</div>
                    </div>
                `;
            }
            document.getElementById('errorsList').innerHTML = errorsHtml;
            
            // Mostrar dominios fallidos
            const failedDomains = failedResults.map(r => `${r.domain} - ${r.error}`).join('\\n');
            document.getElementById('failedDomainsList').textContent = failedDomains;
        }
        
        function switchTab(tabName) {
            // Ocultar todas las pestañas
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Mostrar pestaña seleccionada
            document.getElementById(tabName + 'Tab').classList.add('active');
            document.querySelector(`[onclick="switchTab('${tabName}')"]`).classList.add('active');
        }
        
        function showDeepAnalysis(results) {
            // Análisis de empresas
            if (results.analysis.companies) {
                showCompanyAnalysis(results.analysis.companies, results.successful);
            }
            
            // Análisis de industrias
            if (results.analysis.industries) {
                showIndustryAnalysis(results.analysis.industries);
            }
            
            // Análisis de performance
            if (results.analysis.performance) {
                showPerformanceAnalysis(results.analysis.performance);
            }
        }
        
        function showCompanyAnalysis(companyData, successfulResults) {
            // Métricas de empresas
            const companyMetricsHtml = `
                <div class="metric-card">
                    <div class="metric-value">${companyData.name_extraction_rate.toFixed(1)}%</div>
                    <div class="metric-label">Nombres Extraídos</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${companyData.enrichment_rate.toFixed(1)}%</div>
                    <div class="metric-label">Con Enrichment</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${companyData.avg_technologies.toFixed(1)}</div>
                    <div class="metric-label">Techs Promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${companyData.avg_social_media.toFixed(1)}</div>
                    <div class="metric-label">Social Promedio</div>
                </div>
            `;
            document.getElementById('companyMetrics').innerHTML = companyMetricsHtml;
            
            // Chart de distribución de tecnologías
            const ctx = document.getElementById('companyChart').getContext('2d');
            const techDist = companyData.tech_distribution;
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(techDist),
                    datasets: [{
                        label: 'Número de Empresas',
                        data: Object.values(techDist),
                        backgroundColor: '#667eea',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución de Tecnologías por Empresa'
                        }
                    }
                }
            });
            
            // Top empresas por tecnologías
            let topCompaniesHtml = '<h3>🏆 Top Empresas por Tecnologías</h3>';
            companyData.top_tech_companies.forEach((company, index) => {
                const percentage = (company.tech_count / companyData.max_technologies) * 100;
                topCompaniesHtml += `
                    <div class="list-item">
                        <span class="list-rank">${index + 1}</span>
                        <span class="list-name">${company.company_name || company.domain}</span>
                        <div class="item-bar">
                            <div class="item-fill" style="width: ${percentage}%"></div>
                        </div>
                        <span class="list-value">${company.tech_count} techs</span>
                    </div>
                `;
            });
            document.getElementById('topCompanies').innerHTML = topCompaniesHtml;
        }
        
        function showIndustryAnalysis(industryData) {
            if (industryData.message) {
                document.getElementById('industryBreakdown').innerHTML = `
                    <div class="alert alert-info">${industryData.message}</div>
                `;
                return;
            }
            
            // Chart de industrias
            const ctx = document.getElementById('industryChart').getContext('2d');
            const topIndustries = Object.entries(industryData.top_industries).slice(0, 8);
            
            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: topIndustries.map(([name]) => name),
                    datasets: [{
                        data: topIndustries.map(([, count]) => count),
                        backgroundColor: [
                            '#667eea', '#764ba2', '#4caf50', '#f44336', 
                            '#ff9800', '#9c27b0', '#2196f3', '#00bcd4'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución por Industrias'
                        }
                    }
                }
            });
            
            // Breakdown de industrias
            let industryHtml = `
                <h3>📊 Breakdown de Industrias</h3>
                <div class="insight-box">
                    <h4>📈 Estadísticas</h4>
                    <div class="insight-item">🎯 ${industryData.industry_detection_rate.toFixed(1)}% de empresas con industria detectada</div>
                    <div class="insight-item">🏭 ${Object.keys(industryData.top_industries).length} industrias diferentes encontradas</div>
                </div>
            `;
            
            Object.entries(industryData.industry_distribution).forEach(([industry, data]) => {
                industryHtml += `
                    <div class="list-item">
                        <span class="item-name">${industry}</span>
                        <div class="item-bar">
                            <div class="item-fill" style="width: ${data.percentage}%"></div>
                        </div>
                        <span class="item-value">${data.count} (${data.percentage.toFixed(1)}%)</span>
                    </div>
                `;
            });
            document.getElementById('industryBreakdown').innerHTML = industryHtml;
        }
        
        function showPerformanceAnalysis(perfData) {
            // Métricas de performance
            const performanceMetricsHtml = `
                <div class="metric-card">
                    <div class="metric-value">${perfData.avg_scan_time.toFixed(2)}s</div>
                    <div class="metric-label">Tiempo Promedio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${perfData.min_scan_time.toFixed(2)}s</div>
                    <div class="metric-label">Más Rápido</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${perfData.max_scan_time.toFixed(2)}s</div>
                    <div class="metric-label">Más Lento</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">${perfData.avg_success_time.toFixed(2)}s</div>
                    <div class="metric-label">Promedio Exitosos</div>
                </div>
            `;
            document.getElementById('performanceMetrics').innerHTML = performanceMetricsHtml;
            
            // Chart de distribución de tiempos
            const ctx = document.getElementById('performanceChart').getContext('2d');
            
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: Object.keys(perfData.time_distribution),
                    datasets: [{
                        label: 'Número de Scans',
                        data: Object.values(perfData.time_distribution),
                        backgroundColor: ['#4caf50', '#8bc34a', '#ff9800', '#f44336'],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Distribución de Tiempos de Scan'
                        }
                    }
                }
            });
            
            // Insights de performance
            let insightsHtml = '<div class="insight-box"><h4>⚡ Performance Insights</h4>';
            perfData.performance_insights.forEach(insight => {
                insightsHtml += `<div class="insight-item">${insight}</div>`;
            });
            insightsHtml += '</div>';
            
            // Extremos de performance
            insightsHtml += `
                <h3>🏃‍♂️ Extremos de Performance</h3>
                <div class="list-item">
                    <span class="item-name">🚀 Dominio más rápido:</span>
                    <span class="item-value">${perfData.fastest_domain.domain} (${perfData.fastest_domain.time.toFixed(2)}s)</span>
                </div>
                <div class="list-item">
                    <span class="item-name">🐌 Dominio más lento:</span>
                    <span class="item-value">${perfData.slowest_domain.domain} (${perfData.slowest_domain.time.toFixed(2)}s)</span>
                </div>
            `;
            
            // Recrear el contenido del tab de performance
            document.getElementById('performanceTab').innerHTML = 
                `<div class="metrics-grid">${performanceMetricsHtml}</div>
                 <div class="chart-container"><canvas id="performanceChart"></canvas></div>
                 ${insightsHtml}`;
            
            // Re-crear el chart después de recrear el contenedor
            setTimeout(() => {
                const newCtx = document.getElementById('performanceChart').getContext('2d');
                new Chart(newCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(perfData.time_distribution),
                        datasets: [{
                            label: 'Número de Scans',
                            data: Object.values(perfData.time_distribution),
                            backgroundColor: ['#4caf50', '#8bc34a', '#ff9800', '#f44336'],
                            borderRadius: 8
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            title: {
                                display: true,
                                text: 'Distribución de Tiempos de Scan'
                            }
                        }
                    }
                });
            }, 100);
        }
        
        function showAlert(message, type) {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${type}`;
            alertDiv.textContent = message;
            
            document.querySelector('.container').insertBefore(alertDiv, document.querySelector('.section'));
            
            setTimeout(() => {
                alertDiv.remove();
            }, 5000);
        }
    </script>
</body>
</html>
        """

def run_analyzer(host: str = "0.0.0.0", port: int = 8080):
    """Ejecuta el analizador de success rate"""
    analyzer = SuccessAnalyzer()
    
    print(f"\n🎯 Success Rate Analyzer iniciado")
    print(f"📍 URL: http://{host}:{port}")
    print(f"📊 Sube un CSV con dominios para analizar el success rate")
    
    uvicorn.run(analyzer.app, host=host, port=port)

if __name__ == "__main__":
    run_analyzer()