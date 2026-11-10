# -*- coding: utf-8 -*-
"""세순이 계산기 v0.5.36 - PySide6 UI. 납부지연가산세는 참고용 추산."""
import json
import os
import sys
import calendar
import webbrowser
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP, localcontext
from pathlib import Path

from PySide6.QtCore import Qt, QDate, QTimer, Signal, QSize, QEvent, QRegularExpression
from PySide6.QtGui import QIcon, QPixmap, QPainter, QKeyEvent, QPalette, QColor, QRegularExpressionValidator
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QStackedWidget, QDateEdit, QLineEdit, QMessageBox,
    QSizePolicy, QScrollArea, QGraphicsDropShadowEffect, QDialog, QCalendarWidget, QStyle, QAbstractSpinBox)

BG = '#f5f8fd'
CONFIG = Path(os.getenv('APPDATA') or Path.home()) / 'DateCalculatorKR' / 'settings.json'
ASSETS = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))


def fmt(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite(): return '오류'
        text = format(number, 'f').rstrip('0').rstrip('.') if '.' in format(number, 'f') else format(number, 'f')
        left, sep, right = text.partition('.')
        return f'{int(left):,}' + ('.' + right if sep else '')
    except Exception:
        return '오류'


def fmt_arithmetic_result(value):
    """Only *display* at most three decimal places; retain full Decimal precision."""
    try:
        number = Decimal(str(value))
        if not number.is_finite():
            return '오류'
        with localcontext() as ctx:
            ctx.prec = max(50, len(number.as_tuple().digits) + 4)
            rounded = number.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
        return fmt(rounded)
    except (InvalidOperation, ValueError):
        return '오류'


def trunc(value): return int(Decimal(value).to_integral_value(rounding=ROUND_DOWN))

def tax_trunc(value):
    """원단위 절사: 1원 자리 미만이 아닌 1원 자리를 버려 10원 단위로 정리."""
    return trunc(Decimal(value) / Decimal(10)) * 10


def full_months(start, end):
    if end <= start: return 0
    months = (end.year-start.year)*12 + end.month-start.month
    anniversary = min(start.day, calendar.monthrange(end.year,end.month)[1])
    return max(0,months-(end.day < anniversary))


def tax_calculation(amount, start, end):
    days = (end-start).days
    if days < 0: raise ValueError('종료일은 시작일보다 빠를 수 없습니다.')
    a = abs(Decimal(str(amount)))
    if not a.is_finite() or a > Decimal('1e18'): raise ValueError('계산 가능한 금액을 초과했습니다.')
    # 가산세 계산 기준이 되는 본세는 원 미만 소수 부분을 먼저 절사합니다.
    a = Decimal(trunc(a))
    local = a * Decimal('.1')
    months = min(full_months(start,end),60)
    nm = months if a>=1500000 else 0
    lm = months if local>=450000 else 0
    return days, (tax_trunc(a*Decimal('.00022')*days), tax_trunc(local*Decimal('.00022')*days),
        tax_trunc(a*(Decimal('.03')+Decimal('.0067')*nm)) if days else 0,
        tax_trunc(local*(Decimal('.03')+Decimal('.0066')*lm)) if days else 0), (a,local,a,local), (nm,lm)


STYLE = """
QMainWindow, QWidget#root { background: #f5f8fd; color:#152237; font-family:'Malgun Gothic','Segoe UI'; }
QLabel { background: transparent; color:#172337; }
QFrame#display { background:#e7f3ff; border:1px solid #d3e4f5; border-radius:10px; }
QFrame#divider { background:#dbe5ef; }
QPushButton { border:1px solid #e0e6ef; border-radius:8px; background:#ffffff; color:#111b2c; font-size:15px; }
QPushButton:hover { background:#e7f2ff; border-color:#bdd9f5; }
QPushButton:pressed { background:#d3e7ff; }
QPushButton#operation { background:#e9eef6; }
QPushButton#equals { background:#0867db; color:white; font-weight:700; }
QPushButton#equals:hover {background:#005bc5;}
QPushButton#memory { border:1px solid #dce5f0; background:#f4f8fd; border-radius:7px; font-size:11px; color:#354766; }
QPushButton#tab {border:0; border-bottom:3px solid transparent; border-radius:0; background:transparent; font-size:11px; color:#53647c; font-weight:700; padding:4px 1px;}
QPushButton#tab[active='true'] { color:#0966d2; border-bottom:3px solid #0874e6; }
QPushButton#favicon {border:1px solid #e7ebf1; background:white; border-radius:8px;}
QPushButton#history { border:0; border-bottom:1px solid #e5ebf4; border-radius:0; background:transparent; text-align:left; font-size:13px; padding:8px; }
QPushButton#history:hover {background:#e2effd;}
QPushButton#clear {background:#edf3fb; font-size:11px; padding:5px;}
QLineEdit#dateInput { background:white; color:#152237; selection-color:white; selection-background-color:#0874e6; border:1px solid #cfdbea; border-radius:7px; padding:6px; font-size:12px; }
QScrollArea, QWidget#historyEntries, QWidget#qt_scrollarea_viewport { background:transparent; color:#172337; }
QScrollBar:vertical {background:#eff4fa;border:0;border-radius:5px;width:8px;margin:0;}
QScrollBar::handle:vertical {background:#a8bdd4;border:0;border-radius:4px;min-height:27px;}
QScrollBar::handle:vertical:hover {background:#4e91d9;}
QScrollBar::handle:vertical:pressed {background:#1670ce;}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {height:0px;border:0;background:none;}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {background:transparent;}

QCalendarWidget { background:white; color:#152237; }
QCalendarWidget QWidget { background:white; color:#152237; }
QCalendarWidget QToolButton {background:#e9f1fb;color:#152237;}
QFrame#day {background:#e7f3ff; border-radius:9px; border:1px solid #d5e6f8;}
QFrame#pct {background:#f2f7fd; border:1px solid #e0eaf6; border-radius:7px;}
QFrame#taxblue {background:#e7f3ff; border-radius:8px;}
QFrame#taxgreen {background:#e6f7ef; border-radius:8px;}
QFrame#notice {background:#eff5fc; border:1px solid #dfeaf7; border-radius:8px;}
"""


class TaxRow(QFrame):
    def __init__(self, title, index, callback):
        super().__init__()
        self.setObjectName('taxblue' if index%2==0 else 'taxgreen')
        self.setCursor(Qt.PointingHandCursor)
        self.formula = ''
        self.callback = callback
        box=QHBoxLayout(self); box.setContentsMargins(10,3,10,3);box.setSpacing(4)
        left=QVBoxLayout();left.setSpacing(1)
        heading=QLabel(title);heading.setStyleSheet('font-size:13px;font-weight:700;')
        self.eq=QLabel('');self.eq.setStyleSheet('font-size:11px;color:#51637d;')
        self.eq.setTextInteractionFlags(Qt.NoTextInteraction)
        left.addWidget(heading);left.addWidget(self.eq)
        self.value=QLabel('0');self.value.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.value.setStyleSheet('font-size:17px;font-weight:700;')
        box.addLayout(left,1);box.addWidget(self.value)
        for label in (heading,self.eq,self.value):label.setAttribute(Qt.WA_TransparentForMouseEvents,True)
    def mouseReleaseEvent(self,event):
        if event.button()==Qt.LeftButton and self.formula:self.callback(self.formula)
        super().mouseReleaseEvent(event)
    def set_values(self, formula, value):
        self.formula=formula;self.eq.setText(formula);self.value.setText(fmt(value))


# 2026-10-26 reference points for family count 1, monthly taxable pay (KRW).
# These checkpoints are NOT a complete official withholding table. Intermediate
# values are estimates, explicitly marked as such in the UI.
WITHHOLDING_ONE_PERSON_POINTS = (
    (0, 0), (2000000, 19520), (2500000, 35600),
    (3000000, 74350), (3500000, 127220), (4000000, 195960),
    (5000000, 335470), (6000000, 505900), (7000000, 732700),
)


def estimate_wage_withholding_one_person(monthly_pay):
    """Estimated wage withholding (national income tax) from published sample rows.

    This is NOT an exact NTS table lookup. The upper limit is deliberately
    bounded rather than inventing figures for high earnings.
    """
    pay = int(max(Decimal(0), Decimal(str(monthly_pay))))
    points = WITHHOLDING_ONE_PERSON_POINTS
    if pay > points[-1][0]:
        return None
    for (left, left_tax), (right, right_tax) in zip(points, points[1:]):
        if left <= pay <= right:
            if pay == left: return tax_trunc(left_tax)
            if pay == right: return tax_trunc(right_tax)
            return tax_trunc(Decimal(left_tax) + Decimal(right_tax-left_tax)*Decimal(pay-left)/Decimal(right-left))
    return 0


def show_styled_help(parent, title, message, table=None):
    """Compact branded modal with optional rendered rate table."""
    dlg=QDialog(parent)
    dlg.setWindowTitle(title)
    dlg.setMinimumWidth(310)
    dlg.setStyleSheet("QDialog{background:#f6f9ff;color:#192b44;} QLabel{color:#20354f;}"
                      "QPushButton#confirm{background:#0969da;border:0;border-radius:9px;color:white;"
                      "font-size:12px;font-weight:700;padding:8px 28px;}"
                      "QPushButton#confirm:hover{background:#075abe;}")
    v=QVBoxLayout(dlg);v.setContentsMargins(14,12,14,12);v.setSpacing(9)
    heading=QLabel(title);heading.setStyleSheet('font-size:14px;font-weight:750;color:#0966d2;')
    v.addWidget(heading)
    if message:
        desc=QLabel(message);desc.setWordWrap(True);desc.setStyleSheet('font-size:11px;')
        v.addWidget(desc)
    if table:
        frame=QFrame();frame.setStyleSheet('QFrame{background:white;border:1px solid #dbe6f4;border-radius:0px;}')
        grid=QGridLayout(frame);grid.setContentsMargins(3,3,3,3);grid.setSpacing(1)
        for r,row in enumerate(table):
            for c,item in enumerate(row):
                lbl=QLabel(str(item));lbl.setAlignment(Qt.AlignCenter if r==0 else (Qt.AlignLeft if c==0 else Qt.AlignRight))
                lbl.setStyleSheet(f"font-size:11.33px;background:{'#dfedff' if r==0 else ('#fff' if r%2 else '#f0f6ff')};padding:4px 2px;font-weight:{'700' if r==0 else '500'};")
                grid.addWidget(lbl,r,c)
        v.addWidget(frame)
    row=QHBoxLayout();row.addStretch()
    ok=QPushButton('확인');ok.setObjectName('confirm');ok.clicked.connect(dlg.accept)
    row.addWidget(ok);row.addStretch();v.addLayout(row)
    dlg.exec()


def percent_text(rate):
    value = Decimal(str(rate)) * 100
    return f'{value.normalize():f}'.rstrip('0').rstrip('.') + '%' if '.' in f'{value.normalize():f}' else f'{value.normalize():f}%'


def bracket_table(brackets):
    result=[('과세표준','세율','누진공제')]
    old=0
    for limit,rate,deduction in brackets:
        label=(f'{fmt(old)}원 초과' if old else '')
        if limit is not None:
            label += (' ~ ' if old else '')+fmt(limit)+'원'+(' 이하' if not old else '')
        result.append((label, percent_text(rate), fmt(deduction)+'원' if deduction else '-'))
        if limit is not None: old=limit
    return result


def numeric_like(value):
    t=str(value).replace(',','').replace(' ','').replace('원','').replace('%','').replace('-','').replace('.','')
    return bool(t) and t.replace('억','').replace('만','').isdigit()


class CopyImageBlock(QFrame):
    """Reference section: one click places its rendered section image on clipboard."""
    def __init__(self, title, body, copier):
        super().__init__()
        self.setObjectName('notice')
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip('클릭하면 이 영역을 이미지로 복사합니다.')
        self.copier = copier
        self.title = title
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(3)
        header = QLabel(title)
        header.setStyleSheet('font-size:11px;font-weight:700;color:#0966d2;')
        self.header_row = QHBoxLayout()
        self.header_row.setContentsMargins(0, 0, 0, 0)
        self.header_row.setSpacing(3)
        self.header_row.addWidget(header)
        self.header_label = header
        layout.addLayout(self.header_row)
        self.body = QLabel(body)
        self.body.setWordWrap(True)
        self.body.setTextFormat(Qt.PlainText)
        self.body.setStyleSheet('font-size:11px;color:#26374c;')
        layout.addWidget(self.body)
        for child in (header, self.body):
            child.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    def set_body(self, body):
        self.body.setText(body)

    def add_help(self, help_text):
        """A real clickable help icon; independent of the parent image-copy action."""
        button = QPushButton('ⓘ', self)
        button.setFixedSize(20,20)
        button.setFocusPolicy(Qt.NoFocus)
        button.setCursor(Qt.PointingHandCursor)
        button.setToolTip('근로소득세 도움말')
        button.setStyleSheet('QPushButton{background:#e1efff;border:1px solid #bdd6f5;border-radius:10px;'
                             'color:#0966d2;font-size:12px;font-weight:bold;padding:0;}')
        button.clicked.connect(lambda: QMessageBox.information(self, '근로소득세 안내', help_text))
        self.header_row.addWidget(button,0)
        self.help_button = button

    def set_grid(self, headers, rows, totals=None, subtitle=None, append=False, helps=None, center_values=False, column_stretch=None, align_cells=None):
        """Dense blue tables, centered headings/text and right-aligned numerals."""
        self.body.hide()
        if not append:
            self.header_label.setVisible(False)  # header table replaces repeated title
        if not hasattr(self, '_table_holder'):
            self._table_holder=QWidget(self)
            self.layout().addWidget(self._table_holder)
            self._table_layout=QVBoxLayout(self._table_holder)
            self._table_layout.setContentsMargins(0,1,0,0);self._table_layout.setSpacing(3)
        if not append:
            while self._table_layout.count():
                item=self._table_layout.takeAt(0)
                if item.widget():item.widget().deleteLater()
        frame=QFrame(self._table_holder)
        frame.setObjectName('ratesGrid')
        frame.setStyleSheet('QFrame#ratesGrid{background:#fff;border:1px solid #dfe9f6;border-radius:0px;}')
        grid=QGridLayout(frame);grid.setContentsMargins(2,2,2,2);grid.setSpacing(1)
        for r,row in enumerate([headers]+rows):
            for c,val in enumerate(row):
                key=(r,c)
                is_help=bool(helps and key in helps)
                if is_help:
                    widget=QPushButton(str(val)+' ⓘ',frame)
                    widget.setMinimumWidth(0)
                    h_title,h_text,h_table=helps[key]
                    widget.clicked.connect(lambda _=False,t=h_title,m=h_text,tab=h_table:show_styled_help(self,t,m,tab))
                    widget.setCursor(Qt.PointingHandCursor);widget.setFocusPolicy(Qt.NoFocus)
                    if self.title=="최저임금": widget.setContentsMargins(0,0,0,0)
                else:
                    widget=QLabel(str(val),frame)
                    widget.setAlignment((align_cells.get(c, Qt.AlignCenter) if align_cells and r>0 else (Qt.AlignRight if self.title in ('근로소득세','사업소득세') and (c==1 or (c==2 and r>0)) else Qt.AlignCenter if center_values or r==0 or not numeric_like(val) else Qt.AlignRight)))
                    widget.setWordWrap(len(str(val)) > 23)
                    widget.setMinimumWidth(0)
                    widget.setAttribute(Qt.WA_TransparentForMouseEvents,True)
                bg='#dfeeff' if r==0 else ('#fff' if r%2 else '#f2f7ff')
                fg=('#075bc8' if c==len(row)-1 else '#172b48') if self.title in ('근로소득세','사업소득세') else ('#355271' if r==0 else ('#075bc8' if c==len(row)-1 else '#172b48'))
                if self.title in ('근로소득세','사업소득세'):
                    bg = '#e5f5ee' if c==2 else ('#dfeeff' if r==0 else '#fff')
                vertical_pad='5px' if self.title in ('기장의무 판단 기준','성실신고확인대상사업자 기준','최저임금','전자세금계산서 발급대상') else '4px'
                widget.setStyleSheet(f'text-align:{"center" if self.title=="4대보험료" else "left" if is_help and r>0 and c==0 else "center"};font-size:10.33px;font-weight:{"500" if (self.title in ("근로소득세","사업소득세") or r>0) else "700"};color:{fg};background:{bg};border:0;border-radius:0px;padding:{vertical_pad} 1px;')
                grid.addWidget(widget,r,c)
        for c in range(len(headers)):grid.setColumnStretch(c, (column_stretch[c] if column_stretch else 1))
        self._table_layout.addWidget(frame)
        if subtitle:
            label=QLabel(subtitle);label.setWordWrap(True)
            label.setStyleSheet('font-size:10.33px;color:#536987;')
            label.setAttribute(Qt.WA_TransparentForMouseEvents,True)
            self._table_layout.addWidget(label)
        if totals:
            bar=QFrame();bar.setStyleSheet('QFrame{background:#e7f2ff;border:0;border-radius:0px;}')
            line=QHBoxLayout(bar);line.setContentsMargins(4,3,4,3)
            for title,value in totals:
                col=QVBoxLayout();col.setSpacing(0)
                lab=QLabel(title);lab.setStyleSheet('font-size:10.33px;color:#536985;')
                num=QLabel(value);num.setStyleSheet('font-size:12.33px;font-weight:700;color:#0966d2;')
                for x in (lab,num):
                    x.setAlignment(Qt.AlignCenter)
                    x.setAttribute(Qt.WA_TransparentForMouseEvents,True)
                col.addWidget(lab);col.addWidget(num);line.addLayout(col,1)
            bar.setAttribute(Qt.WA_TransparentForMouseEvents,True)
            self._table_layout.addWidget(bar)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            self.copier(self)
        super().mouseReleaseEvent(event)


def progressive_tax(amount, brackets):
    amount = max(Decimal('0'), abs(Decimal(str(amount))))
    for limit, rate, deduction in brackets:
        if limit is None or amount <= limit:
            return tax_trunc(amount * Decimal(str(rate)) - Decimal(str(deduction))), rate, deduction
    return 0, 0, 0


INCOME_BRACKETS = [
    (14000000, '.06', 0), (50000000, '.15', 1260000),
    (88000000, '.24', 5760000), (150000000, '.35', 15440000),
    (300000000, '.38', 19940000), (500000000, '.40', 25940000),
    (1000000000, '.42', 35940000), (None, '.45', 65940000),
]
CORPORATE_BRACKETS = [
    (200000000, '.10', 0), (20000000000, '.20', 20000000),
    (300000000000, '.22', 420000000), (None, '.25', 9420000000),
]


def rate_text(brackets):
    lines = []
    previous = 0
    for limit, rate, deduction in brackets:
        if previous == 0:
            name = f'{fmt(limit)}원 이하' if limit is not None else '전체'
        else:
            name = f'{fmt(previous)}원 초과' + (f' ~ {fmt(limit)}원' if limit is not None else '')
        lines.append(f'{name}  |  {percent_text(rate)}  |  누진공제 {fmt(deduction)}원')
        if limit is not None:
            previous = limit
    return '\n'.join(lines)


class DateCalculator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('세순이 계산기 v0.5.36')
        # 계산기 화면 클릭 시 날짜 입력창에서 키보드 포커스를 옮길 수 있도록 함.
        self.setFocusPolicy(Qt.StrongFocus)
        self.resize(640,504)
        self.setMinimumSize(620,485)
        icon=ASSETS/'date_calculator.ico'
        if icon.exists():self.setWindowIcon(QIcon(str(icon)))
        self.setStyleSheet(STYLE)
        self.typed='0';self.operand=None;self.operator=None;self.expression='';self.new_entry=True;self.is_arithmetic_result=False
        self.memory=Decimal('0');self.memory_set=False;self.history=[];self.saved_start=date(date.today().year,1,1);self.history_pending=False
        self._load_config()
        # 시작날짜는 저장된 날짜보다 실행 연도의 1월 1일을 우선합니다.
        self.saved_start=date(date.today().year,1,1)
        self._build_ui();self.update_display()
        QApplication.instance().installEventFilter(self)

    def _load_config(self):
        try:
            cfg=json.loads(CONFIG.read_text(encoding='utf-8'))
            self.saved_start=date.fromisoformat(cfg.get('start','2026-08-01'))
            self.history=[x for x in cfg.get('history',[]) if isinstance(x,dict) and 'expression' in x and 'value' in x][-13:]
        except (OSError,ValueError,TypeError):pass

    def closeEvent(self,event):
        try:
            CONFIG.parent.mkdir(parents=True,exist_ok=True)
            CONFIG.write_text(json.dumps({'start':self.get_input_date(self.start).isoformat() if hasattr(self, 'start') else self.saved_start.isoformat(),'history':self.history[-13:]},ensure_ascii=False,indent=2),encoding='utf-8')
        except OSError:pass
        super().closeEvent(event)

    def _build_ui(self):
        root=QWidget();root.setObjectName('root');self.setCentralWidget(root)
        main=QHBoxLayout(root);main.setContentsMargins(7,6,7,6);main.setSpacing(6)
        left=QWidget();left.setMinimumWidth(282);right=QWidget();right.setMinimumWidth(285)
        main.addWidget(left,49);main.addWidget(right,51)
        l=QVBoxLayout(left);l.setContentsMargins(0,0,0,0);l.setSpacing(5)
        display=QFrame();display.setObjectName('display')
        d=QVBoxLayout(display);d.setContentsMargins(10,6,10,6);d.setSpacing(3)
        self.exp_label=QLabel('');self.exp_label.setAlignment(Qt.AlignRight)
        self.exp_label.setStyleSheet('font-size:11px;color:#506784;')
        self.display=QLabel('0');self.display.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        self.display.setStyleSheet('font-size:32px;font-weight:750;')
        d.addWidget(self.exp_label);d.addWidget(self.display,1)
        # QLabel은 일반적으로 클릭해도 키보드 포커스를 가져오지 않는다.
        # 표시창 어디를 클릭하든 날짜 편집을 끝내고 계산기로 전환.
        self.calculator_display_frame = display
        for focus_target in (display, self.exp_label, self.display):
            focus_target.installEventFilter(self)
        display.setFixedHeight(82)
        l.addWidget(display)
        self.memory_status=QLabel('')
        self.memory_status.setStyleSheet('font-size:11px;color:#0966d2;')
        self.memory_status.setFixedHeight(13)
        self.memory_status.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        branding=QHBoxLayout(); branding.setContentsMargins(0,0,0,0);branding.setSpacing(4)
        branding.addWidget(self.memory_status,1)
        brand=QLabel('tokis.tistory.com'); brand.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        brand.setStyleSheet('font-size:9px;color:#8493a8;'); brand.setFixedHeight(13)
        branding.addWidget(brand)
        l.addLayout(branding)
        keys=QGridLayout();keys.setHorizontalSpacing(4);keys.setVerticalSpacing(4);l.addLayout(keys,1)
        for col,k in enumerate(('MC','MR','M+','M−')):
            b=QPushButton(k);b.setObjectName('memory');b.setFocusPolicy(Qt.NoFocus);b.setMinimumHeight(29);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding);b.clicked.connect(lambda _=False,x=k:self.act(x));keys.addWidget(b,0,col)
        layout=[('%','CE','C','⌫'),('7','8','9','÷'),('4','5','6','×'),('1','2','3','−'),('+/−','0','.','+'),('000','=','', '')]
        for row,items in enumerate(layout,1):
            for col,k in enumerate(items):
                if not k:continue
                b=QPushButton(k);b.setFocusPolicy(Qt.NoFocus);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Expanding)
                if k=='=':
                    b.setObjectName('equals')
                    b.setMinimumHeight(31)
                elif k in ('÷','×','−','+','%'):b.setObjectName('operation')
                b.clicked.connect(lambda _=False,x=k:self.act(x));keys.addWidget(b,row,2 if k=='=' else col,1,2 if k in ('000','=') else 1)
        for col in range(4): keys.setColumnStretch(col,1)
        keys.setRowMinimumHeight(0,29);keys.setRowStretch(0,1)
        for row in range(1,7):
            keys.setRowMinimumHeight(row,34)
            keys.setRowStretch(row,1)

        r=QVBoxLayout(right);r.setContentsMargins(0,0,0,0);r.setSpacing(3)
        top=QHBoxLayout();top.setSpacing(1)
        self.tabs=[]
        for text,name in [('세율등','rates'),('날짜계산','date'),('계산기록','history')]:
            b=QPushButton(text);b.setObjectName('tab');b.setCursor(Qt.PointingHandCursor);b.setFocusPolicy(Qt.NoFocus)
            iconfile=ASSETS/('history_tab.png' if name=='history' else 'calendar_tab.png')
            if name == 'rates':
                # 날짜계산 탭과 동일한 Qt 아이콘+문자 간격 적용
                rate_icon=QPixmap(11,11);rate_icon.fill(Qt.transparent)
                painter=QPainter(rate_icon);painter.setPen(QColor('#53647c'))
                painter.drawText(rate_icon.rect(),Qt.AlignCenter,'％');painter.end()
                b.setIcon(QIcon(rate_icon));b.setIconSize(QSize(11,11))
            else:
                b.setIcon(QIcon(str(iconfile)));b.setIconSize(QSize(11,11))
            b.setMinimumWidth(0);b.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Fixed)
            b.clicked.connect(lambda _=False,n=name:self.switch_tab(n));top.addWidget(b,1);self.tabs.append(b)
        self.clear_history_button=QPushButton()
        self.clear_history_button.setObjectName('favicon')
        self.clear_history_button.setFixedSize(25,28)
        self.clear_history_button.setFocusPolicy(Qt.NoFocus)
        self.clear_history_button.setToolTip('계산 기록 전체 삭제')
        self.clear_history_button.setCursor(Qt.PointingHandCursor)
        self.clear_history_button.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self.clear_history_button.setIconSize(QSize(17,17))
        self.clear_history_button.clicked.connect(self.clear_history)
        top.addWidget(self.clear_history_button)
        for name,filename,url in [('Gmail','gmail_fallback.png','https://mail.google.com/'),('다음','daum_fallback.png','https://mail.daum.net/'),('네이버','naver_fallback.png','https://mail.naver.com/')]:
            b=QPushButton();b.setObjectName('favicon');b.setFixedSize(27,28);b.setFocusPolicy(Qt.NoFocus);b.setToolTip(name+' 메일 열기')
            path=ASSETS/filename
            if path.exists():b.setIcon(QIcon(str(path)));b.setIconSize(QPixmap(str(path)).size().boundedTo(QSize(21, 21)))
            else:b.setText(name[:1])
            b.clicked.connect(lambda _=False,u=url:webbrowser.open(u));top.addWidget(b)
            if name == '다음':self.daum_button=b
        r.addLayout(top)
        # 다음 아이콘은 동봉된 이미지 파일만 사용합니다. 실행 시 네트워크에 접속하지 않습니다.
        self.stack=QStackedWidget();r.addWidget(self.stack,1)
        self.history_panel=QWidget();self.rates_panel=QWidget();self.date_panel=QWidget()
        self.stack.addWidget(self.rates_panel);self.stack.addWidget(self.date_panel);self.stack.addWidget(self.history_panel)
        # 초기 화면에 필요한 세율 탭부터 구성합니다. 다른 탭은 최초 진입 시 생성합니다.
        self._build_rates()
        self.toast=QLabel('', self.stack);self.toast.setAlignment(Qt.AlignCenter)
        self.toast.setStyleSheet('background:#23334a;color:white;border-radius:8px;padding:8px;font-size:12px;')
        self.toast.hide()
        self.switch_tab('rates')

    def _build_history(self):
        outer=QVBoxLayout(self.history_panel);outer.setContentsMargins(0,0,0,0)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea {background:transparent;border:0;} QScrollArea > QWidget > QWidget {background:transparent;} QScrollArea QWidget#qt_scrollarea_viewport {background:transparent;}')
        self.entries=QWidget();self.entries.setObjectName('historyEntries');self.entries.setStyleSheet('background:transparent;color:#172337;')
        self.entry_layout=QVBoxLayout(self.entries)
        self.entry_layout.setContentsMargins(0,0,0,0);self.entry_layout.setSpacing(0)
        scroll.setWidget(self.entries);outer.addWidget(scroll,1)
        self.render_history()

    def _build_date(self):
        v=QVBoxLayout(self.date_panel);v.setContentsMargins(0,3,0,0);v.setSpacing(9)
        range_line=QHBoxLayout();range_line.setSpacing(9)
        self.start=QLineEdit(self.saved_start.isoformat())
        self.end=QLineEdit(date.today().isoformat())
        for widget in (self.start,self.end):
            widget.setObjectName('dateInput')
            widget.setAlignment(Qt.AlignCenter)
            widget.setMaxLength(10)
            # 숫자 8자리 또는 YYYY-MM-DD만 허용합니다. 날짜 입력 완료 시 계산기로 포커스를 이동합니다.
            widget.setValidator(QRegularExpressionValidator(
                QRegularExpression(r'(?:[0-9]{0,8}|[0-9]{0,4}-[0-9]{0,2}-[0-9]{0,2})'), widget))
            widget.textEdited.connect(lambda _text, w=widget: self._date_edited(w))
            widget.setPlaceholderText('YYYY-MM-DD')
            widget.setToolTip('날짜를 YYYY-MM-DD 형식으로 입력하거나 오른쪽 달력을 선택하세요.')
            widget.textChanged.connect(self.update_tax)
            widget.editingFinished.connect(lambda w=widget:self.normalize_input_date(w))
            group=QHBoxLayout();group.setSpacing(2);group.setContentsMargins(0,0,0,0)
            group.addWidget(widget,1)
            cal_btn=QPushButton();cal_btn.setIcon(QIcon(str(ASSETS/'calendar_tab.png')))
            cal_btn.setIconSize(QSize(21,21));cal_btn.setToolTip('달력에서 날짜 선택');cal_btn.setFixedSize(38,36)
            cal_btn.setFocusPolicy(Qt.NoFocus)
            cal_btn.clicked.connect(lambda _=False,w=widget,b=cal_btn:self.open_calendar(w,b))
            group.addWidget(cal_btn)
            range_line.addLayout(group,1)
            if widget is self.start:
                sep=QLabel('~');sep.setAlignment(Qt.AlignCenter);range_line.addWidget(sep)
        v.addLayout(range_line)
        panel=QFrame();panel.setObjectName('day');box=QVBoxLayout(panel);box.setContentsMargins(4,4,4,4)
        self.days_label=QLabel('0 일');self.days_label.setAlignment(Qt.AlignCenter)
        self.days_label.setStyleSheet('font-size:28px;font-weight:750;')
        box.addWidget(self.days_label);panel.setFixedHeight(51);v.addWidget(panel)
        pct_line=QHBoxLayout();pct_line.setSpacing(5)
        self.ten=QLabel('0');self.twenty=QLabel('0')
        for text,label in [('10%',self.ten),('20%',self.twenty)]:
            tag=QLabel(text);tag.setAlignment(Qt.AlignCenter)
            tag.setStyleSheet('background:#e5f1ff;color:#0967db;border-radius:6px;padding:8px;font-weight:700;font-size:14px;')
            label.setAlignment(Qt.AlignCenter);label.setStyleSheet('background:white;border:1px solid #dae5f2;border-radius:6px;padding:8px;font-weight:700;font-size:14px;')
            pct_line.addWidget(tag,2);pct_line.addWidget(label,3)
        v.addLayout(pct_line)
        self.tax_rows=[]
        for index,title in enumerate(('신고분 (국세)','신고분 (지방세)','고지분 (국세)','고지분 (지방세)')):
            row=TaxRow(title,index,self.copy_formula);row.setMinimumHeight(51);v.addWidget(row,1);self.tax_rows.append(row)
        notice=QFrame();notice.setObjectName('notice');note=QVBoxLayout(notice);note.setContentsMargins(9,5,9,5)
        self.notice=QLabel('일 단위 규정등이 적용될 수 있습니다. 이전 고지분은 종전 규정이 적용될 수 있습니다.')
        self.notice.setWordWrap(True);self.notice.setStyleSheet('font-size:10px;color:#53647c;')
        note.addWidget(self.notice);v.addWidget(notice)
        self.warning=QLabel('');self.warning.setWordWrap(True);self.warning.setStyleSheet('font-size:10px;color:#ae3b43;')
        self.warning.hide();v.addWidget(self.warning)

    @staticmethod
    def get_input_date(editor):
        return date.fromisoformat(editor.text().strip())

    def _date_edited(self, editor):
        """유효한 날짜 숫자 8자리를 직접 입력한 직후 계산기 키 입력으로 전환."""
        raw = editor.text().strip()
        digits = raw.replace('-', '')
        if len(digits) != 8 or not digits.isascii() or not digits.isdigit():
            return
        # 포맷 도중 임의로 날짜를 만들지 않고, 유효성 검사를 통과한 날짜만 확정합니다.
        try:
            parsed = date(int(digits[:4]), int(digits[4:6]), int(digits[6:8]))
            if parsed.year < 1900:
                return
        except ValueError:
            return
        editor.setText(parsed.isoformat())
        # QLineEdit의 이벤트 처리가 끝난 다음에 포커스를 이동합니다.
        QTimer.singleShot(0, self.setFocus)

    def normalize_input_date(self, editor):
        try:
            d=self.get_input_date(editor)
            if d.year<1900: raise ValueError('지원하는 연도는 1900년 이후입니다.')
            editor.setText(d.isoformat())
        except ValueError:
            pass   # 입력값을 임의로 바꾸지 않고 수정할 수 있게 유지

    def open_calendar(self, editor, button):
        popup=QDialog(self, Qt.Popup)
        popup.setStyleSheet('QDialog {background:white;border:1px solid #cfdbea;}')
        layout=QVBoxLayout(popup);layout.setContentsMargins(5,5,5,5)
        calendar_widget=QCalendarWidget(popup)
        calendar_widget.setGridVisible(True)
        calendar_widget.setMinimumDate(QDate(1900,1,1))
        try:
            selected=self.get_input_date(editor)
        except ValueError:
            selected=date.today()
        calendar_widget.setSelectedDate(QDate(selected.year,selected.month,selected.day))
        layout.addWidget(calendar_widget)
        def chosen(chosen_date):
            editor.setText(chosen_date.toString('yyyy-MM-dd'))
            popup.accept()
        calendar_widget.clicked.connect(chosen)
        popup.move(button.mapToGlobal(button.rect().bottomLeft()))
        popup.exec()

    def switch_tab(self, tab):
        old = getattr(self, 'active_main_tab', None)
        self.active_main_tab = tab
        # 표시 전 한 번만 탭을 생성하여 시작 시 위젯 구성 시간을 줄입니다.
        if tab == 'date' and not hasattr(self, 'tax_rows'):
            self._build_date()
            self.update_tax()
        elif tab == 'history' and not hasattr(self, 'entry_layout'):
            self._build_history()
        index = {'rates': 0, 'date': 1, 'history': 2}[tab]
        if tab == 'rates' and old != 'rates':
            self.switch_rate_page(0)
        self.stack.setCurrentIndex(index)
        self.clear_history_button.setVisible(tab == 'history')
        for button, name in zip(self.tabs, ('rates', 'date', 'history')):
            button.setProperty('active', str(name == tab).lower())
            button.style().unpolish(button)
            button.style().polish(button)
        self.setFocus()

    def switch_rate_page(self, index):
        self.rates_stack.setCurrentIndex(index)
        for i, button in enumerate(self.rate_tabs):
            button.setProperty('active', str(i == index).lower())
            button.style().unpolish(button)
            button.style().polish(button)
        self.setFocus()

    def show_copy_toast(self):
        # Child overlay of the tab stack: never participates in layout resizing.
        self.toast.adjustSize()
        width=min(self.stack.width()-12, max(190,self.toast.sizeHint().width()+10))
        width=max(1,width)
        self.toast.setGeometry(max(0,(self.stack.width()-width)//2),
                               max(0,self.stack.height()-self.toast.sizeHint().height()-10),
                               width,self.toast.sizeHint().height())
        self.toast.raise_()
        self.toast.show()
        QTimer.singleShot(2000, self.toast.hide)

    def copy_image(self, widget):
        # Capture only the selected section, not the calculator, tabs or surrounding UI.
        pixmap = widget.grab()
        if widget is self.rate_blocks.get('근로소득세'):
            insurance = self.rate_blocks['4대보험료'].grab()
            if not insurance.isNull() and not pixmap.isNull():
                width = max(insurance.width(), pixmap.width())
                joined = QPixmap(width, insurance.height()+pixmap.height())
                joined.fill(Qt.white)
                painter = QPainter(joined)
                painter.drawPixmap(0,0,insurance)
                painter.drawPixmap(0,insurance.height(),pixmap)
                painter.end()
                pixmap = joined
        if not pixmap.isNull():
            QApplication.clipboard().setPixmap(pixmap)
            self.toast.setText('✓ 이미지가 복사되었습니다.')
            self.show_copy_toast()
        self.setFocus()

    def _build_rates(self):
        outer=QVBoxLayout(self.rates_panel);outer.setContentsMargins(0,0,0,0);outer.setSpacing(5)
        header=QHBoxLayout();header.setSpacing(3);self.rate_tabs=[]
        for i,title in enumerate(('세율','기장의무','양도상증')):
            b=QPushButton(title);b.setObjectName('tab');b.setFocusPolicy(Qt.NoFocus)
            b.setCursor(Qt.PointingHandCursor);b.setMinimumWidth(0)
            b.clicked.connect(lambda _=False,n=i:self.switch_rate_page(n))
            b.setStyleSheet('QPushButton{border:1px solid #dbe6f3;border-radius:6px;background:#e9f2ff;font-size:11px;font-weight:700;padding:4px 0;color:#35516d;}QPushButton[active="true"]{background:#0969da;color:white;border-color:#0969da;}')
            header.addWidget(b,1);self.rate_tabs.append(b)
        outer.addLayout(header);self.rates_stack=QStackedWidget();outer.addWidget(self.rates_stack,1)
        self.rate_blocks={}
        for titles in (
            ('4대보험료','근로소득세','사업소득세','종합소득세','법인세'),
            ('기장의무 판단 기준','성실신고확인대상사업자 기준','최저임금','전자세금계산서 발급대상'),
            ('양도소득세율','장기보유특별공제','증여세율','증여재산공제','상속세율','상속공제'),
        ):
            scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            contents=QWidget();v=QVBoxLayout(contents);v.setContentsMargins(0,0,2,0);v.setSpacing(1 if len(self.rate_blocks)==0 else 5)
            for title in titles:
                block=CopyImageBlock(title,'',self.copy_image)
                if titles[0]=='4대보험료':
                    block.layout().setContentsMargins(6,3,6,3)
                v.addWidget(block);self.rate_blocks[title]=block
            v.addStretch(1);scroll.setWidget(contents);self.rates_stack.addWidget(scroll)
        tables={
            '기장의무 판단 기준':(('기장의무','복식부기','단순경비율 기준'),[
                ('도소매 등','3억 이상','6천만 미만'),('제조·건설·음숙 등','1억 5천만 이상','3,600만 미만'),
                ('임대·서비스 등','7,500만 이상','2,400만 미만')],None),
            '성실신고확인대상사업자 기준':(('성실신고확인대상사업자 기준','해당 연도 수입금액'),[
                ('도소매 등','15억 원 이상'),
                ('제조·건설·음식숙박 등','7억 5천만 원 이상'),
                ('임대·서비스 등','5억 원 이상')],
                None),
            '최저임금':(('최저임금','2027년 기준'),[
                ('시급','10,700원'),('주 40시간 월환산','2,236,300원')],None),
            '전자세금계산서 발급대상':(('전자 발급의무','사업장별'),[
                ('세금계산서','직전연도 과·면세 공급가액 8천만 원 이상'),
                ('(면세)계산서','직전연도 총수입금액 8천만 원 이상')],None),
            '양도소득세율':(('양도세 과세표준','세율','누진공제'),[
                ('1,400만 원 이하','6%','-'),('~5천만 원','15%','126만'),
                ('~8,800만 원','24%','576만'),('~1억 5천만 원','35%','1,544만'),
                ('~3억 원','38%','1,994만'),('~5억 원','40%','2,594만'),
                ('~10억 원','42%','3,594만'),('10억 원 초과','45%','6,594만')],None),
            '장기보유특별공제':(('장기보유특별공제','공제 내용'),[
                ('일반 토지·건물','3년 6% → 15년 이상 최대 30%'),
                ('1세대 1주택 특례','보유 최대 40% + 거주 최대 40%')],None),
            '증여세율':(('증여세 과세표준','세율','누진공제'),[
                ('1억 원 이하','10%','-'),('~5억 원','20%','1천만'),
                ('~10억 원','30%','6천만'),('~30억 원','40%','1억 6천만'),
                ('30억 원 초과','50%','4억 6천만')],None),
            '증여재산공제':(('증여재산공제','10년 합산 공제'),[
                ('배우자','6억 원'),('직계존속','5천만 원 (미성년 2천만)'),
                ('직계비속','5천만 원'),('기타 친족','1천만 원')],None),
            '상속세율':(('상속세 과세표준','세율','누진공제'),[
                ('1억 원 이하','10%','-'),('~5억 원','20%','1천만'),
                ('~10억 원','30%','6천만'),('~30억 원','40%','1억 6천만'),
                ('30억 원 초과','50%','4억 6천만')],None),
            '상속공제':(('상속공제','공제금액·기준'),[
                ('기초공제','2억 원'),('자녀 인적공제','1인당 5천만 원'),
                ('미성년자','1천만 원 × 19세까지 잔여연수'),
                ('연로자','65세 이상 1인당 5천만 원'),
                ('장애인','1천만 원 × 기대여명연수'),
                ('일괄공제','5억 또는 기초+인적공제 합계 중 큰 금액'),
                ('배우자 상속공제','최소 5억 · 한도 최대 30억')],None),
        }
        for title,(heads,rows,note) in tables.items():
            helps={}
            if title=='전자세금계산서 발급대상':
                helps[(0,0)]=('전자 발급 의무 안내','다음 해 7월 1일부터 적용',None)
            if title=='최저임금':
                helps[(2,0)]=('주 40시간 월환산','주 40시간 근무 및 유급 주휴시간을 포함하여 월 209시간으로 환산한 금액입니다.',None)
            if title=='상속공제':
                helps[(6,0)]=('일괄공제 적용 불가','배우자 단독으로 상속받은 경우에는 일괄공제를 적용받을 수 없으며, 기초공제(2억원 및 가업·영농상속공제 포함)와 그 밖의 인적공제의 합계액으로만 공제받을 수 있습니다.',None)
            self.rate_blocks[title].set_grid(heads,rows,subtitle=note,helps=helps,
                center_values=(title in ('증여재산공제','상속공제')),
                column_stretch=(6,14) if title=='전자세금계산서 발급대상' else (11,9) if title=='성실신고확인대상사업자 기준' else None,
                align_cells=({0:Qt.AlignLeft,1:Qt.AlignRight,2:Qt.AlignRight} if title=='기장의무 판단 기준' else {0:Qt.AlignLeft,1:Qt.AlignRight} if title in ('최저임금','전자세금계산서 발급대상','성실신고확인대상사업자 기준') else {0:Qt.AlignLeft,1:Qt.AlignLeft} if title in ('장기보유특별공제','상속공제') else {0:Qt.AlignLeft} if title in ('양도소득세율','증여세율','증여재산공제','상속세율') else None))
        self.switch_rate_page(0);self.update_rate_values()

    def update_rate_values(self):
        if not hasattr(self, 'rate_blocks'):
            return
        try:
            amount = abs(Decimal(self.typed))
            if not amount.is_finite():return
            # 세금과 근로·사업 차인지급액 계산에 사용할 원금은 원 미만을 버립니다.
            # 계산기 입력값과 4대보험료 산정 기준은 기존대로 유지합니다.
            taxable_amount = Decimal(trunc(amount))
            # Insurance: calculator amount is monthly pay; industrial accident is industry-specific.
            pension_base = min(max(amount, Decimal(410000)), Decimal(6590000)) if amount else Decimal(0)
            pension = tax_trunc(pension_base * Decimal('.0475'))
            health = tax_trunc(amount * Decimal('.03595'))
            care = tax_trunc(amount * Decimal('.004724'))
            employee_employment = tax_trunc(amount * Decimal('.009'))
            # Apply the employee and employer rounding separately: employer rate is
            # unemployment 0.9% + the currently assumed extra 0.25%.
            employer_employment = tax_trunc(amount * (Decimal('.009') + Decimal('.0025')))
            accident = tax_trunc(amount * Decimal('.0147'))  # illustrative average, not the workplace-specific rate
            worker = pension + health + care + employee_employment
            employer = pension + health + care + employer_employment + accident
            # One person INCLUDING the employee (no other dependents),
            # withholding ratio 100%; salary means monthly taxable pay.
            wage_tax = estimate_wage_withholding_one_person(taxable_amount)
            wage_local = tax_trunc(Decimal(wage_tax) * Decimal('.1')) if wage_tax is not None else None
            business_income_tax = tax_trunc(taxable_amount * Decimal('.03'))
            business_local_tax = tax_trunc(Decimal(business_income_tax) * Decimal('.1'))
            business_total = business_income_tax + business_local_tax
            wage_total = wage_tax + wage_local if wage_tax is not None else None
            net_wage = taxable_amount - worker - wage_total if wage_total is not None else None
            net_business = taxable_amount - business_total
            # Employee and employer totals are calculated using the assumptions below.
            self.rate_blocks['4대보험료'].set_grid(
                ('4대보험','요율','직원','회사'),[
                    ('국민연금','9.5%',fmt(pension),fmt(pension)),
                    ('건강보험','7.19%',fmt(health),fmt(health)),
                    ('장기요양','0.9448%',fmt(care),fmt(care)),
                    ('고용보험','1.8%',fmt(employee_employment),fmt(employer_employment)),
                    ('산재보험','1.47%', '0',fmt(accident)),
                ],totals=(('직원 부담금 합계',fmt(worker)+'원'),('회사 부담금 합계',fmt(employer)+'원'),('전체 총액',fmt(worker+employer)+'원')),
                helps={
                    (4,0):('고용보험 부담 안내','직원 부담: 실업급여 보험료 0.9%\n\n회사 부담: 실업급여 보험료 0.9%\n고용안정·직업능력개발사업 0.25~0.85%\n\n회사 추가 부담률은 사업장 규모 등에 따라 달라집니다.',None),
                    (5,0):('산재보험 부담 안내','회사 전액 부담\n직원 부담 없음\n\n적용 요율: 표의 1.47%는 평균 추정치입니다.\n실제 요율은 사업장 업종 및 적용 조건에 따라 달라집니다.',None),
                })
            # 근로소득세는 별도 클릭 영역; 클릭하면 4대보험료 영역도 함께 이미지로 복사.
            self.rate_blocks['근로소득세'].set_grid(
                ('근로소득세',fmt(wage_tax)+'원' if wage_tax is not None else '공식표 확인 필요','차인지급액'),[
                    ('지방소득세',fmt(wage_local)+'원' if wage_local is not None else '공식표 확인 필요',
                     fmt(net_wage)+'원' if net_wage is not None else '산정 보류')],
                helps={(0,0):('근로소득세 안내','공제대상 가족 본인 포함 1명, 원천징수 100% 기준입니다. 일부 급여 구간은 추정·보간값을 사용하므로 국세청 간이세액표로 확인해야 합니다.',None)})
            self.rate_blocks['사업소득세'].set_grid(
                ('사업소득세',fmt(business_income_tax)+'원','차인지급액'),[
                    ('지방소득세',fmt(business_local_tax)+'원',fmt(net_business)+'원')],
                helps=None)
            for title,brackets in (('종합소득세',INCOME_BRACKETS),('법인세',CORPORATE_BRACKETS)):
                result,rate,deduction=progressive_tax(taxable_amount,brackets)
                self.rate_blocks[title].set_grid(
                    (title,'세율','누진공제','산출세액'),
                    [(fmt(taxable_amount),percent_text(rate),fmt(deduction),fmt(max(0,result)))],
                    helps={(0,1):(title+' 구간별 세율','2026년 기본 누진세율과 누진공제액',bracket_table(brackets)),
                           (0,3):('산출세액 안내','기본 누진세율을 적용한 산출세액입니다.\n세액공제·감면 및 지방소득세는 포함하지 않았습니다.',None)})
        except (InvalidOperation,ValueError):
            return

    def update_display(self):
        formatted=fmt_arithmetic_result(self.typed) if self.is_arithmetic_result else fmt(self.typed)
        self.display.setText(formatted);self.exp_label.setText(self.expression)
        self.memory_status.setText('M  '+fmt(self.memory) if self.memory_set else '')
        size=32 if len(formatted)<13 else 25 if len(formatted)<18 else 19
        self.display.setStyleSheet(f'font-size:{size}px;font-weight:750;')
        self.update_tax()
        self.update_rate_values()

    @staticmethod
    def calc(a,op,b):
        return {'+':lambda:a+b,'−':lambda:a-b,'×':lambda:a*b,'÷':lambda:a/b}[op]()

    def act(self,key):
        # 날짜 입력 후 숫자/메모리 버튼을 마우스로 눌러도
        # 이후의 키보드 입력은 계산기로 이어져야 한다.
        self.setFocus()
        try:
            if key.isdigit() or key=='.':
                self.is_arithmetic_result=False
                if self.new_entry:
                    self.typed='0';self.new_entry=False;self.history_pending=False
                    if self.operator is None:self.expression=''
                if key=='.':
                    if '.' not in self.typed:self.typed+='.'
                elif len(self.typed.replace('-','').replace('.','')) + len(key) <= 18:
                    self.typed=key.lstrip('0') or '0' if self.typed=='0' else self.typed+key
            elif key=='C':
                self.is_arithmetic_result=False
                self.typed='0';self.operand=None;self.operator=None;self.expression='';self.new_entry=True;self.history_pending=False
            elif key=='CE':self.typed='0';self.new_entry=True;self.history_pending=False;self.is_arithmetic_result=False
            elif key=='⌫':
                self.is_arithmetic_result=False
                if not self.new_entry:
                    self.typed=self.typed[:-1] if len(self.typed)>1 else '0'
                    if self.typed=='-':self.typed='0'
            elif key=='+/−':self.typed=self.typed[1:] if self.typed.startswith('-') else '-'+self.typed
            elif key=='%':
                self.is_arithmetic_result=False
                self.typed=str((self.operand if self.operand is not None else Decimal(1))*Decimal(self.typed)/100)
                self.new_entry=True
            elif key in ('+','−','×','÷'):
                current=Decimal(self.typed)
                if self.operator and (not self.new_entry or self.history_pending):
                    current=self.calc(self.operand,self.operator,current);self.typed=str(current);self.is_arithmetic_result=True
                self.operand=current;self.operator=key;self.expression=f'{fmt(current)} {key}';self.new_entry=True;self.history_pending=False
            elif key=='=' and self.operator and self.operand is not None:
                b=Decimal(self.typed);answer=self.calc(self.operand,self.operator,b)
                expr=f'{fmt(self.operand)} {self.operator} {fmt(b)} ='
                self.typed=str(answer);self.expression=expr;self.is_arithmetic_result=True
                self.history.append({'expression':expr,'value':self.typed});self.history=self.history[-13:]
                self.render_history();self.operand=None;self.operator=None;self.new_entry=True;self.history_pending=False
            elif key=='MC':
                self.memory=Decimal(0);self.memory_set=False
            elif key=='MR':
                if self.memory_set:
                    self.typed=str(self.memory)
                    self.is_arithmetic_result=False
                    if self.operator is None:
                        self.operand=None;self.expression=''
                    self.new_entry=True
                    self.history_pending=self.operator is not None
            elif key=='M+':
                self.memory+=Decimal(self.typed)
                self.memory_set=True
                self.new_entry=True
            elif key=='M−':
                self.memory-=Decimal(self.typed)
                self.memory_set=True
                self.new_entry=True
            self.update_display()
        except (InvalidOperation,ZeroDivisionError,OverflowError,ValueError):
            QMessageBox.warning(self,'계산 오류','계산할 수 없는 식입니다.')
            self.typed='0';self.operand=None;self.operator=None;self.expression='';self.new_entry=True;self.history_pending=False;self.is_arithmetic_result=False
            self.update_display()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self,'toast') and self.toast.isVisible():
            self.toast.adjustSize()
            width=min(self.stack.width()-12,max(190,self.toast.sizeHint().width()+10))
            self.toast.setGeometry(max(0,(self.stack.width()-width)//2),
                                   max(0,self.stack.height()-self.toast.sizeHint().height()-10),
                                   max(1,width),self.toast.sizeHint().height())

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.MouseButtonPress
                and watched in (self.calculator_display_frame, self.exp_label, self.display)
                and event.button() == Qt.LeftButton):
            # 날짜 QLineEdit에 남은 포커스를 계산기 메인 창으로 이전.
            self.setFocus()
            # 마우스 이벤트 자체는 기존 위젯으로 전달한다.
            return False
        # 백틱(`)은 세율등 하위 탭 전환 전용 (날짜 텍스트 편집 중에는 제외).
        if event.type() == QEvent.KeyPress and (event.key() == Qt.Key_QuoteLeft or event.text() == '`'):
            app = QApplication.instance()
            active = app.activeModalWidget() or app.activePopupWidget()
            if (self.isActiveWindow() and active is None and self.active_main_tab == 'rates'
                    and not isinstance(app.focusWidget(), QLineEdit)):
                self.switch_rate_page((self.rates_stack.currentIndex() + 1) % 3)
                event.accept()
                return True
        # Tab (Shift+Tab 포함): 세율등 / 날짜계산 / 계산기록 전환.
        # 달력 팝업과 다른 대화상자의 기본 키보드 조작은 방해하지 않는다.
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            app = QApplication.instance()
            active = app.activeModalWidget() or app.activePopupWidget()
            if self.isActiveWindow() and active is None and not isinstance(app.focusWidget(), QLineEdit):
                next_page = {'rates':'date','date':'history','history':'rates'}[self.active_main_tab]
                self.switch_tab(next_page)
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self,event:QKeyEvent):
        if isinstance(QApplication.focusWidget(), QLineEdit):
            super().keyPressEvent(event);return
        key=event.text();mapping={'*':'×','/':'÷','-':'−','+':'+','=':'=','%':'%'}
        if key.isdigit() or key=='.' or key in mapping:self.act(mapping.get(key,key));event.accept();return
        if event.key() in (Qt.Key_Enter,Qt.Key_Return):self.act('=');event.accept();return
        if event.key()==Qt.Key_Backspace:self.act('⌫');event.accept();return
        if event.key()==Qt.Key_Escape:self.act('C');event.accept();return
        super().keyPressEvent(event)

    def render_history(self):
        if not hasattr(self,'entry_layout'):return
        while self.entry_layout.count():
            item=self.entry_layout.takeAt(0)
            if item.widget():item.widget().deleteLater()
        for record in reversed(self.history):
            expression,value=record['expression'],record['value']
            b=QPushButton(f'{expression}      {fmt_arithmetic_result(value)}');b.setObjectName('history');b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet('QPushButton {background:transparent;color:#172337;border:0;border-bottom:1px solid #dce6f0;text-align:left;padding:9px;font-size:13px;} QPushButton:hover {background:#e7f2ff;color:#152337;}')
            b.clicked.connect(lambda _=False,v=value:self.restore_history(v))
            self.entry_layout.addWidget(b)
        self.entry_layout.addStretch(1)

    def restore_history(self, value):
        """기록의 수식이 아닌 결과 숫자만 새 계산의 첫 피연산자로 불러온다."""
        try:
            result = Decimal(str(value).replace(',', ''))
            if not result.is_finite():
                return
        except (InvalidOperation, ValueError):
            return
        # 연산자를 이미 선택했다면 기록값은 두 번째 피연산자입니다.
        # 예: 기록 8742 클릭 → ÷ → 기록 276 클릭 → = → 31.673...
        self.typed = str(result)
        self.is_arithmetic_result = True
        if self.operator is None:
            self.expression = ''
            self.operand = None
        else:
            self.expression = f'{fmt(self.operand)} {self.operator}'
        # 불러온 값은 숫자키로 교체할 수 있고, = 또는 연산자로 계산할 수 있습니다.
        self.new_entry = True
        self.history_pending = self.operator is not None
        self.update_display()
        self.setFocus()

    def clear_history(self):
        # 휴지통 클릭 시 확인창 없이 즉시 계산 기록을 삭제합니다.
        if self.history:
            self.history = []
            self.render_history()
        self.setFocus()

    def update_tax(self,*_):
        if not hasattr(self,'tax_rows'):return
        s=self.get_input_date(self.start);e=self.get_input_date(self.end)
        try:
            amount=Decimal(self.typed)
            days, values,bases,months=tax_calculation(amount,s,e)
            self.days_label.setText(f'{days:,} 일')
            base_amount = Decimal(trunc(abs(amount)))
            self.ten.setText(fmt(trunc(base_amount*Decimal('.1'))))
            self.twenty.setText(fmt(trunc(base_amount*Decimal('.2'))))
            for i,row in enumerate(self.tax_rows):
                if i<2:formula=f'{fmt(bases[i])} × {days:,}일 × 0.022% = {fmt(values[i])}'
                else:
                    m=months[i-2];rate='0.67%' if i==2 else '0.66%'
                    formula=f'{fmt(bases[i])} × (3% + {rate} × {m}개월) = {fmt(values[i])}' if days else '0일: 0원'
                row.set_values(formula,values[i])
            self.warning.setText('⚠ 2026-07-01 이전 고지분은 종전규정이 적용될 수 있습니다.')
            self.warning.setVisible(s<date(2026,7,1))
        except (ValueError,InvalidOperation,OverflowError) as exc:
            self.days_label.setText('날짜 확인 필요')
            self.warning.setText(str(exc));self.warning.show()
            for row in self.tax_rows:row.set_values('',0)

    def copy_formula(self,formula):
        QApplication.clipboard().setText(formula)
        self.toast.setText('✓ 계산식이 복사되었습니다.')
        self.show_copy_toast()
        self.setFocus()


def main():
    app=QApplication(sys.argv)
    app.setApplicationName('세순이 계산기')
    app.setStyle('Fusion')
    palette=app.palette()
    palette.setColor(QPalette.Window,QColor('#f5f8fd'))
    palette.setColor(QPalette.Base,QColor('#ffffff'))
    palette.setColor(QPalette.AlternateBase,QColor('#eff5fc'))
    palette.setColor(QPalette.Text,QColor('#172337'))
    palette.setColor(QPalette.ButtonText,QColor('#172337'))
    app.setPalette(palette)
    ico=ASSETS/'date_calculator.ico'
    if ico.exists():app.setWindowIcon(QIcon(str(ico)))
    window=DateCalculator();window.show()
    sys.exit(app.exec())

if __name__=='__main__':main()
