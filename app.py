#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ROI Calculator Web - 投资回报率分析工具
支持Windows和Linux部署
"""

import os
import sys
import time
import requests
import json
from datetime import datetime, timedelta
from io import BytesIO
import base64
import platform

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from roi import ROICalculator

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 配置
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "charts")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_stock_data_tencent(symbol):
    """获取腾讯股价数据"""
    try:
        if symbol.startswith('SH'):
            code = 'sh' + symbol[2:]
        else:
            code = 'sz' + symbol[2:]
        
        url = f'https://qt.gtimg.cn/q={code}'
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        
        parts = response.text.strip().split('~')
        if len(parts) > 46:
            return {
                'name': parts[1],
                'price': float(parts[3]) if parts[3] else 0,
                'pb': float(parts[46]) if parts[46] else 0,
            }
        return None
    except Exception as e:
        print(f"获取股价失败: {e}")
        return None


def get_financial_data(symbol):
    """获取财务数据"""
    try:
        import akshare as ak
        
        if symbol.startswith('SH'):
            akshare_code = symbol[2:] + ".SH"
        else:
            akshare_code = symbol[2:] + ".SZ"
        
        df = ak.stock_financial_analysis_indicator_em(symbol=akshare_code)
        
        if len(df) > 0:
            annual_df = df[df['REPORT_TYPE'].str.contains('年报', na=False)]
            if len(annual_df) > 0:
                latest = annual_df.iloc[0]
                roe = float(latest.get('ROEJQ', 0)) if latest.get('ROEJQ') else 0
                return {'roe': roe}
        return {'roe': 0}
    except Exception as e:
        print(f"获取财务数据失败: {e}")
        return {'roe': 0}


def get_ttm_dividend(symbol):
    """获取TTM股息数据"""
    try:
        import akshare as ak
        
        df = ak.stock_individual_spot_xq(symbol=symbol)
        data = dict(zip(df['item'], df['value']))
        
        ttm_dividend = 0
        ttm_yield = 0
        
        for item, value in data.items():
            if '股息(TTM)' in item:
                ttm_dividend = float(value) if value else 0
            elif '股息率(TTM)' in item:
                ttm_yield = float(value) if value else 0
        
        return {
            'ttm_dividend': round(ttm_dividend, 4),
            'ttm_yield': round(ttm_yield, 4),
        }
    except Exception as e:
        print(f"获取TTM股息失败: {e}")
        return {'ttm_dividend': 0, 'ttm_yield': 0}


def get_chinese_font_path():
    """获取中文字体路径，下载到本地"""
    import requests
    from urllib.request import urlretrieve
    
    font_path = '/tmp/wqy-microhei.ttc'
    
    # 如果字体文件不存在或太小，下载
    if not os.path.exists(font_path) or os.path.getsize(font_path) < 1000:
        try:
            print("下载中文字体...")
            # 使用 wqy-microhei 字体 (文泉驿微米黑)
            url = 'https://github.com/AaronFeng753/Waifu2x-Extension-GUI/raw/master/SRC/Waifu2x-Extension-QT/wqy-microhei.ttc'
            urlretrieve(url, font_path)
            print("字体下载完成")
        except Exception as e:
            print(f"字体下载失败: {e}")
            return None
    
    return font_path if os.path.exists(font_path) else None


def setup_chinese_font():
    """设置中文字体"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    
    system = platform.system()
    
    if system == 'Windows':
        # Windows: 使用系统字体
        available = [f.name for f in fm.fontManager.ttflist]
        for wf in ['Microsoft YaHei', 'SimHei']:
            if wf in available:
                plt.rcParams['font.sans-serif'] = [wf]
                break
    else:
        # Linux: 下载并使用中文字体
        font_path = get_chinese_font_path()
        if font_path:
            fm.fontManager.addfont(font_path)
            font_prop = fm.FontProperties(fname=font_path)
            plt.rcParams['font.sans-serif'] = [font_prop.get_name()]
            plt.rcParams['axes.unicode_minus'] = False
            print(f"使用字体: {font_prop.get_name()}")
        else:
            print("警告: 中文字体加载失败")
    
    return plt


def generate_chart(results):
    """生成分析图表"""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    
    # 设置中文字体
    setup_chinese_font()
    
    # 获取字体用于图表
    system = platform.system()
    if system != 'Windows':
        font_path = get_chinese_font_path()
        font_prop = fm.FontProperties(fname=font_path) if font_path else None
    else:
        font_prop = None
        available = [f.name for f in fm.fontManager.ttflist]
        for wf in ['Microsoft YaHei', 'SimHei']:
            if wf in available:
                font_prop = fm.FontProperties(weight='bold')
                break
    
    names = [r['name'] for r in results]
    f1_values = [r['roi_formula1'] for r in results]
    f2_values = [r['roi_formula2'] for r in results]
    roes = [r['roe'] for r in results]
    prices = [r['price'] for r in results]
    
    colors = ['#4472C4', '#ED7D31', '#70AD47', '#FFC000', '#9BBB59']
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 12))
    fig.suptitle(f'ROI Analysis - {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                 fontsize=16, fontweight='bold')
    
    # 股息率
    ax1 = axes[0, 0]
    bars1 = ax1.bar(names, f1_values, color=colors[:len(names)])
    ax1.set_title('ROI Formula 1: Dividend Yield (%)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Yield (%)')
    ax1.set_ylim(0, max(f1_values) * 1.3 if f1_values else 10)
    for bar, val in zip(bars1, f1_values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f'{val:.2f}%', ha='center', va='bottom', fontsize=10)
    
    # ROE/PB
    ax2 = axes[0, 1]
    bars2 = ax2.bar(names, f2_values, color=colors[:len(names)])
    ax2.set_title('ROI Formula 2: ROE/PB (%)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('ROE/PB (%)')
    ax2.set_ylim(0, max(f2_values) * 1.3 if f2_values else 10)
    for bar, val in zip(bars2, f2_values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                f'{val:.2f}%', ha='center', va='bottom', fontsize=10)
    
    # ROE
    ax3 = axes[1, 0]
    bars3 = ax3.bar(names, roes, color=colors[:len(names)])
    ax3.set_title('ROE (%)', fontsize=12, fontweight='bold')
    ax3.set_ylabel('ROE (%)')
    for bar, val in zip(bars3, roes):
        ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{val:.2f}%', ha='center', va='bottom', fontsize=10)
    
    # Price
    ax4 = axes[1, 1]
    bars4 = ax4.bar(names, prices, color=colors[:len(names)])
    ax4.set_title('Price (yuan)', fontsize=12, fontweight='bold')
    ax4.set_ylabel('Price (yuan)')
    for bar, val in zip(bars4, prices):
        ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 5, 
                f'{val:.2f}', ha='center', va='bottom', fontsize=10)
    
    plt.tight_layout()
    
    beijing_time = datetime.now() + timedelta(hours=8)
    timestamp = beijing_time.strftime('%Y%m%d_%H%M%S')
    filename = f'chart_{timestamp}.png'
    filepath = os.path.join(OUTPUT_DIR, filename)
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filename


# ==================== 辅助函数 ====================

def get_stocks():
    """读取股票配置"""
    try:
        with open('stocks.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return [
            {"name": "东阿阿胶", "symbol": "SZ000423"},
            {"name": "五粮液", "symbol": "SZ000858"},
            {"name": "贵州茅台", "symbol": "SH600519"},
            {"name": "洋河股份", "symbol": "SZ002304"},
        ]


def save_stocks(stocks):
    """保存股票配置"""
    with open('stocks.json', 'w', encoding='utf-8') as f:
        json.dump(stocks, f, ensure_ascii=False, indent=2)


def get_rules():
    """读取规则配置"""
    try:
        with open('rules.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def save_rules(rules):
    """保存规则配置"""
    with open('rules.json', 'w', encoding='utf-8') as f:
        json.dump(rules, f, ensure_ascii=False, indent=2)


def apply_custom_roe(roe, symbol, rules):
    """应用自定义ROE规则"""
    for rule in rules:
        if rule['symbol'] == symbol:
            min_roe = float(rule['min_roe'])
            if roe < min_roe:
                print(f"应用规则: {symbol} ROE {roe}% < {min_roe}%, 使用 {min_roe}%")
                return min_roe
    return roe


# ==================== 路由 ====================

@app.route('/')
def index():
    """首页"""
    return render_template('index.html', stocks=get_stocks(), rules=get_rules())


@app.route('/query', methods=['POST'])
def query():
    """查询股票ROI"""
    symbols = request.form.getlist('symbols')
    
    config_stocks = get_stocks()
    rules = get_rules()
    
    if not symbols:
        symbols = [s['symbol'] for s in config_stocks]
    
    results = []
    calculator = ROICalculator()
    
    for symbol in symbols:
        data = get_stock_data_tencent(symbol)
        if not data:
            continue
        
        fin_data = get_financial_data(symbol)
        ttm_data = get_ttm_dividend(symbol)
        
        price = data['price']
        roe = fin_data['roe']
        pb = data['pb']
        ttm_yield = ttm_data['ttm_yield']
        ttm_dividend = ttm_data['ttm_dividend']
        
        # 应用自定义ROE规则
        original_roe = roe
        roe = apply_custom_roe(roe, symbol, rules)
        
        stock_info = {
            'name': data['name'],
            'symbol': symbol,
            'current_price': price,
            'financial': {'roe': roe, 'pb': pb},
            'dividend_yield': ttm_yield,
            'dividend': {'dividends': [{'cash_div': ttm_dividend}]}
        }
        
        result = calculator.calculate(stock_info)
        
        results.append({
            'name': data['name'],
            'symbol': symbol,
            'price': price,
            'roe': roe,
            'original_roe': original_roe,
            'pb': pb,
            'dividend': ttm_dividend,
            'roi_formula1': result.roi_formula1,
            'roi_formula2': result.roi_formula2,
        })
    
    if results:
        chart_file = generate_chart(results)
        sorted_by_f1 = sorted(results, key=lambda x: x['roi_formula1'], reverse=True)
        sorted_by_f2 = sorted(results, key=lambda x: x['roi_formula2'], reverse=True)
        
        return render_template('result.html', 
                             results=results,
                             chart_url=f'/static/charts/{chart_file}',
                             sorted_by_f1=sorted_by_f1,
                             sorted_by_f2=sorted_by_f2)
    
    return render_template('result.html', error="无法获取股票数据")


@app.route('/add_stock', methods=['POST'])
def add_stock():
    """添加股票"""
    name = request.form.get('name', '').strip()
    symbol = request.form.get('symbol', '').strip().upper()
    
    if not name or not symbol:
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="请填写股票名称和代码")
    
    if not symbol.startswith(('SZ', 'SH')):
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="股票代码必须以 SZ 或 SH 开头")
    
    stocks = get_stocks()
    
    for s in stocks:
        if s['symbol'] == symbol:
            return render_template('index.html', stocks=stocks, rules=get_rules(), message=f"股票 {symbol} 已存在")
    
    stocks.append({'name': name, 'symbol': symbol})
    save_stocks(stocks)
    
    return render_template('index.html', stocks=stocks, rules=get_rules(), message=f"已添加 {name} ({symbol})")


@app.route('/delete_stock')
def delete_stock():
    """删除股票"""
    symbol = request.args.get('symbol', '').strip()
    
    if not symbol:
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="股票代码不能为空")
    
    stocks = get_stocks()
    
    for i, s in enumerate(stocks):
        if s['symbol'] == symbol:
            name = s['name']
            del stocks[i]
            save_stocks(stocks)
            return render_template('index.html', stocks=stocks, rules=get_rules(), message=f"已删除 {name} ({symbol})")
    
    return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message=f"股票 {symbol} 不存在")


@app.route('/add_rule', methods=['POST'])
def add_rule():
    """添加ROE规则"""
    symbol = request.form.get('symbol', '').strip().upper()
    min_roe = request.form.get('min_roe', '').strip()
    
    if not symbol or not min_roe:
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="请填写股票代码和最低ROE")
    
    if not symbol.startswith(('SZ', 'SH')):
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="股票代码必须以 SZ 或 SH 开头")
    
    try:
        min_roe = float(min_roe)
    except:
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="最低ROE必须为数字")
    
    rules = get_rules()
    
    for rule in rules:
        if rule['symbol'] == symbol:
            rule['min_roe'] = min_roe
            save_rules(rules)
            return render_template('index.html', stocks=get_stocks(), rules=rules, message=f"已更新 {symbol} 最低ROE为 {min_roe}%")
    
    rules.append({'symbol': symbol, 'min_roe': min_roe})
    save_rules(rules)
    
    return render_template('index.html', stocks=get_stocks(), rules=rules, message=f"已添加 {symbol} 最低ROE: {min_roe}%")


@app.route('/delete_rule')
def delete_rule():
    """删除ROE规则"""
    symbol = request.args.get('symbol', '').strip()
    
    if not symbol:
        return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message="股票代码不能为空")
    
    rules = get_rules()
    
    for i, rule in enumerate(rules):
        if rule['symbol'] == symbol:
            del rules[i]
            save_rules(rules)
            return render_template('index.html', stocks=get_stocks(), rules=rules, message=f"已删除 {symbol} 的ROE规则")
    
    return render_template('index.html', stocks=get_stocks(), rules=get_rules(), message=f"规则 {symbol} 不存在")


@app.route('/api/query', methods=['POST'])
def api_query():
    """API接口"""
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        if not symbols:
            return jsonify({'error': '请提供股票代码列表'})
        
        results = []
        calculator = ROICalculator()
        rules = get_rules()
        
        for symbol in symbols:
            stock_data = get_stock_data_tencent(symbol)
            if not stock_data:
                continue
            
            fin_data = get_financial_data(symbol)
            ttm_data = get_ttm_dividend(symbol)
            
            price = stock_data['price']
            roe = fin_data['roe']
            pb = stock_data['pb']
            ttm_yield = ttm_data['ttm_yield']
            ttm_dividend = ttm_data['ttm_dividend']
            
            roe = apply_custom_roe(roe, symbol, rules)
            
            stock_info = {
                'name': stock_data['name'],
                'symbol': symbol,
                'current_price': price,
                'financial': {'roe': roe, 'pb': pb},
                'dividend_yield': ttm_yield,
                'dividend': {'dividends': [{'cash_div': ttm_dividend}]}
            }
            
            result = calculator.calculate(stock_info)
            
            results.append({
                'name': stock_data['name'],
                'symbol': symbol,
                'price': price,
                'roe': roe,
                'pb': pb,
                'dividend': ttm_dividend,
                'dividend_yield': ttm_yield,
                'roi_formula1': result.roi_formula1,
                'roi_formula2': result.roi_formula2,
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': (datetime.now() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)})


if __name__ == '__main__':
    print("=" * 60)
    print(f"  ROI Calculator - Web Version")
    print(f"  系统: {platform.system()}")
    print(f"  访问: http://localhost:5000")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
