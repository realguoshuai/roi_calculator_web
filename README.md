# 投资回报率统计器 (ROI Calculator)

## 项目概述 

一个用于计算股票投资回报率的命令行工具，支持两种回报率计算口径（股息率和ROE/PB），可导出Excel报告和图表。

## 功能特性 

- **双口径ROI计算**：股息率(LTM)和ROE/PB两种评估方式
- **多数据源聚合**：腾讯(实时价格) + akshare(财务数据) 
- **自动生成报告**：Excel表格 + 3张分析图表
- **灵活配置**：支持外部JSON配置文件自定义股票列表
- **自定义ROE**：可覆盖接口获取的ROE数据 

## 快速开始

### 环境要求

- Python 3.12+
- Windows 10/11

### 安装依赖

```bash
cd D:\code\git\roi_calculator
venv312\Scripts\pip install -r requirements.txt
```

### 运行程序

```bash
# 方式一：直接运行Python脚本
venv312\Scripts\python.exe main_fast.py

# 方式二：双击批处理文件
start.bat
```

### 构建exe

```bash
build.bat
```

输出：`dist/ROI_Calculator/ROI_Calculator.exe`

---

## 详细设计

### 项目结构

```
D:\code\git\roi_calculator\
├── main_fast.py           # 极速版主程序
├── main_enhanced.py       # 增强版主程序
├── roi.py                 # ROI计算核心类
├── config.py              # 内置配置
├── stocks.json            # 外部股票配置（可选）
├── requirements.txt       # Python依赖
├── build.bat              # 构建exe脚本
├── start.bat              # 启动脚本
├── start_enhanced.bat     # 启动增强版
├── ROI_Calculator.spec    # PyInstaller配置
├── data/
│   ├── output/            # 输出目录
│   └── log/               # 日志目录
└── venv312/               # Python虚拟环境
```

### 核心类设计

#### ROIResult类

```python
class ROIResult:
    def __init__(self, stock_name: str, symbol: str, current_price: float,
                 dividend_per_share: float, roe: float, pb: float,
                 roi_formula1: float, roi_formula2: float):
        self.stock_name = stock_name      # 股票名称
        self.symbol = symbol              # 股票代码
        self.current_price = current_price  # 当前股价
        self.dividend_per_share = dividend_per_share  # 每股分红
        self.roe = roe                    # 净资产收益率(%)
        self.pb = pb                      # 市净率
        self.roi_formula1 = roi_formula1  # 公式一：股息率(%)
        self.roi_formula2 = roi_formula2  # 公式二：ROE/PB(%)
        self.data_source = 'N/A'          # 数据来源
        self.dividend_source = 'N/A'      # 分红数据来源
        self.pb_source = 'N/A'            # PB数据来源
        self.interim_dividend = 0         # 中期分红（增强版）
        self.annual_dividend = 0          # 年度分红（增强版）
        self.guaranteed_note = ''         # 保底分红备注（增强版）
```

#### ROICalculator类

```python
class ROICalculator:
    def calculate(self, stock_data: Dict[str, Any]) -> ROIResult:
        """
        计算投资回报率

        输入格式:
        {
            'name': '股票名称',
            'symbol': 'SZ000858',
            'current_price': 100.0,
            'financial': {'roe': 15.0, 'pb': 3.0},
            'dividend_yield': 2.5,      # 可选，股息率(%)
            'dividend': {'dividends': [{'cash_div': 2.5}]}  # 可选
        }

        返回: ROIResult对象
        """

    def _get_dividend_per_share(self, dividend_data: Dict) -> float:
        """从dividend数据中提取每股分红"""

    def _calc_roi_formula1(self, dividend: float, price: float) -> float:
        """公式一：股息率 = (分红 / 股价) × 100%"""

    def _calc_roi_formula2(self, roe: float, pb: float) -> float:
        """公式二：ROE/PB = ROE ÷ PB (ROE不带百分号)"""
```

---

## 数据源

### 股价数据

| 项目 | 说明 |
|------|------|
| 接口 | 腾讯实时行情API |
| URL | `https://qt.gtimg.cn/q={code}` |
| 代码 | `get_stock_data_tencent()` |

#### 字段映射

```python
# 腾讯API返回格式：以~分隔
# 示例: v_sz000858="51~五粮液~000858~27.78~..."

parts = response.text.split('~')

parts[1]  # 股票名称
parts[3]  # 当前价格
parts[39] # 市盈率(PE)
parts[46] # 市净率(PB) ← v2.1修复：原错误使用parts[38]（换手率）
```

#### 返回格式

```python
{
    'name': str,      # 股票名称
    'price': float,   # 当前价格
    'pe': float,      # 市盈率
    'pb': float,      # 市净率
    'source': 'Tencent'
}
```

### 财务数据(ROE/BPS)

| 项目 | 说明 |
|------|------|
| 接口 | akshare `stock_financial_analysis_indicator_em` |
| 代码 | `get_financial_data_akshare()` |

#### ROE优先级

1. **自定义ROE** → `config.py` 中 `CUSTOM_ROE`
2. **年报ROE** → `REPORT_TYPE` 包含"年报"的记录
3. **季度ROE** → 使用最新财报数据

#### 字段映射

```python
df = ak.stock_financial_analysis_indicator_em(symbol="000858.SZ")

df.columns include:
- 'REPORT_TYPE'     # 报表类型：年报/中报/季报
- 'REPORT_DATE'     # 报表日期
- 'ROEJQ'           # 净资产收益率(加权) - 使用此字段
- 'BPS'             # 每股净资产
```

#### 返回格式

```python
{
    'roe': float,        # ROE(%)
    'bps': float,        # 每股净资产
    'report_date': str,  # 报表日期
    'source': str        # 数据来源描述
}
```

### 分红数据

#### 极速版(TTM股息率)

| 项目 | 说明 |
|------|------|
| 接口 | akshare `stock_individual_spot_xq` |
| 代码 | `get_ttm_dividend_xq()` |

```python
df = ak.stock_individual_spot_xq(symbol="000858")
# 返回格式: item/value对

# 查找字段:
# - '股息(TTM)' -> ttm_dividend
# - '股息率(TTM)' -> ttm_yield
```

#### 增强版(年度分红)

| 项目 | 说明 |
|------|------|
| 接口 | akshare `stock_fhps_em` |
| 日期参数 | `date='20250630'` (2025中期), `date='20241231'` (2024年度) |

```python
# 获取2024年度分红
df = ak.stock_fhps_em(date='20241231')
# 列: 代码, 名称, 送股, 转股, 派息, 股息率(%), 股权登记日, 每股分红

df.iloc[0].iloc[5]  # 股息率(%)
df.iloc[0].iloc[7]  # 每股分红(元)
```

#### LTM计算公式

```
LTM = 2024年度分红 - 2024中期分红 + 2025中期分红
```

因为2024年度分红已包含2024年中期分红，所以需要减去重复部分。

---

## 配置

### 股票列表配置

#### 方式一：外部配置文件(stocks.json)

文件位置：与exe或脚本同级目录

```json
[
    {"name": "东阿阿胶", "symbol": "SZ000423"},
    {"name": "五粮液", "symbol": "SZ000858"},
    {"name": "贵州茅台", "symbol": "SH600519"},
    {"name": "洋河股份", "symbol": "SZ002304"},
    {"name": "格力电器", "symbol": "SZ000651"}
]
```

#### 方式二：内置配置(config.py)

```python
STOCKS = [
    {"name": "东阿阿胶", "symbol": "SZ000423"},
    {"name": "五粮液", "symbol": "SZ000858"},
    {"name": "贵州茅台", "symbol": "SH600519"},
    {"name": "洋河股份", "symbol": "SZ002304"}
]
```

**优先级**：外部配置文件 > 内置配置

### 自定义ROE

用于覆盖akshare获取的ROE数据：

```python
CUSTOM_ROE = {
    "SZ002304": 20.0,  # 洋河股份ROE自定义20%
}
```

### 保底分红备注

```python
GUARANTEED_DIVIDEND_NOTES = {
    "SH600519": "【保底分红】贵州茅台：需查阅公司公告确认是否有未来三年保底分红承诺",
    "SZ000858": "【保底分红】五粮液：需查阅公司公告确认是否有未来三年保底分红承诺",
}
```

---

## 输出文件

### Excel文件

路径：`data/output/roi_YYYYMMDD_HHMMSS.xlsx`

| 字段 | 说明 |
|------|------|
| Name | 股票名称 |
| Code | 股票代码 |
| Price | 当前股价(元) |
| ROE(%) | 净资产收益率 |
| PB | 市净率 |
| LTM Dividend | 最近12个月分红(元) |
| Yield(%) | 股息率 |
| ROE/PB(%) | ROE/PB回报率 |
| Data Source | 数据来源 |

### 图表文件

| 文件 | 说明 |
|------|------|
| `ROI_1_YYYYMMDD_HHMMSS.png` | 口径1分析（股息率、ROE、股价、分红） |
| `ROI_2_YYYYMMDD_HHMMSS.png` | 口径2分析（ROE/PB、ROE、股价、PB） |
| `ROI_YYYYMMDD_HHMMSS.png` | 综合对比图 |

---

## 计算公式

### 公式一：股息率

```
股息率 = (每股分红 / 当前股价) × 100%
```

### 公式二：ROE/PB

```
ROE/PB = ROE ÷ PB × 100%
说明：ROE不带百分号直接相除
示例：ROE=15.45%, PB=4.41 → 15.45 / 4.41 = 3.50%
```

### LTM分红

```
LTM = 2024年度分红 - 2024中期分红 + 2025中期分红
```

---

## 依赖说明

```
requests>=2.31.0       # HTTP请求
openpyxl>=3.1.0        # Excel操作
matplotlib>=3.6.0      # 图表生成
numpy>=1.23.0          # 数值计算
jqdatasdk>=1.8.0       # 聚宽数据(可选)
akshare>=1.11.0        # 财经数据接口
```

---

## 版本历史

### v2.1 (2026-01-22)
- PB（市净率）改为直接从腾讯API获取（下标46）
- 修复原PB字段错误问题（原使用下标38，实际是换手率）
- 更新README文档

### v2.0 (2026-01-16)
- 使用akshare `stock_individual_spot_xq` 接口获取TTM股息数据
- 简化数据源，统一使用雪球TTM数据
- 更新PNG文件命名规则

### v1.0
- 初始版本
- 使用akshare `stock_fhps_em` 接口获取分红数据
- 支持LTM和年度两种分红口径

---

## 代码实现要点

### 1. 腾讯API解析

```python
def get_stock_data_tencent(symbol: str) -> dict:
    # 转换代码格式
    if symbol.startswith('SH'):
        code = 'sh' + symbol[2:]
    else:
        code = 'sz' + symbol[2:]
    
    # 请求API
    url = f'https://qt.gtimg.cn/q={code}'
    response = requests.get(url, timeout=10)
    
    # 解析数据
    text = response.text.strip()
    parts = text.split('~')
    
    if len(parts) > 46:
        return {
            'name': parts[1],
            'price': float(parts[3]) if parts[3] else 0,
            'pe': float(parts[39]) if parts[39] else 0,
            'pb': float(parts[46]) if parts[46] else 0,
        }
    return None
```

### 2. ROE获取

```python
def get_financial_data_akshare(symbol: str) -> dict:
    import akshare as ak
    
    # 转换代码格式
    akshare_code = symbol[2:] + ".SH"  # or .SZ
    
    # 获取财务指标
    df = ak.stock_financial_analysis_indicator_em(symbol=akshare_code)
    
    # 优先使用自定义ROE
    custom_roe = get_custom_roe(symbol)
    if custom_roe is not None:
        bps = float(df.iloc[0].get('BPS', 0))
        return {'roe': custom_roe, 'bps': bps}
    
    # 获取年报ROE
    annual_df = df[df['REPORT_TYPE'].str.contains('年报', na=False)]
    if len(annual_df) > 0:
        latest = annual_df.iloc[0]
        return {
            'roe': float(latest.get('ROEJQ', 0)),
            'bps': float(latest.get('BPS', 0)),
        }
    
    return None
```

### 3. ROI计算

```python
class ROICalculator:
    def calculate(self, stock_data: dict) -> ROIResult:
        price = stock_data['current_price']
        roe = stock_data['financial']['roe']
        pb = stock_data['financial']['pb']
        
        # 公式一：股息率
        dividend_yield = stock_data.get('dividend_yield', 0)
        if dividend_yield > 0:
            roi_formula1 = dividend_yield
        else:
            dividend = stock_data['dividend']['dividends'][0]['cash_div']
            roi_formula1 = (dividend / price) * 100
        
        # 公式二：ROE/PB
        roi_formula2 = roe / pb if pb > 0 else 0
        
        return ROIResult(...)
```

### 4. Excel导出

```python
def save_to_excel(results, output_dir, timestamp):
    from openpyxl import Workbook
    
    wb = Workbook()
    ws = wb.active
    ws.title = "ROI Analysis"
    
    # 写入表头
    headers = ["Name", "Code", "Price", "ROE(%)", "PB", "LTM Dividend", "Yield(%)", "ROE/PB(%)"]
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)
    
    # 写入数据
    for row_idx, r in enumerate(results, 2):
        ws.cell(row=row_idx, column=1, value=r.stock_name)
        # ... 其他字段
    
    # 保存
    wb.save(f"{output_dir}/roi_{timestamp}.xlsx")
```

### 5. 图表生成

```python
def save_chart(results, output_dir, timestamp):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    
    # 数据准备
    names = [r.stock_name for r in results]
    f1_values = [r.roi_formula1 if r.roi_formula1 else 0 for r in results]
    
    # 绑制图表
    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.bar(names, f1_values, color=['#4472C4', '#ED7D31', '#70AD47'])
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, height, f'{height:.2f}%',
                ha='center', va='bottom')
    
    # 保存
    fig.savefig(f"{output_dir}/ROI_{timestamp}.png", dpi=150, bbox_inches='tight')
```

---

## 常见问题

### Q: PB值为0？
A: 可能是腾讯API返回的PB字段为空，检查下标是否为46

### Q: ROE获取失败？
A: 检查akshare接口是否正常，尝试使用自定义ROE覆盖

### Q: 如何添加新股票？
A: 编辑`stocks.json`或`config.py`，添加股票名称和代码

### Q: 构建exe失败？
A: 确保虚拟环境完整，运行`build.bat`前先安装所有依赖
