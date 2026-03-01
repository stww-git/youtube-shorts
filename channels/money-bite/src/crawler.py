"""
Money Bite 채널 금융 토픽 크롤러 (한국어 버전)

금융/투자 교육 YouTube Shorts용 주제 데이터베이스
카테고리:
- 금융 용어 (finance-terms)
- 투자 기초 (investment-basics)
- 주식 시장 (stock-market)
- 재테크 팁 (personal-finance)
- 역사적 수익 (historical-returns)
"""

import os
import json
import logging
import random
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

CHANNEL_DIR = Path(__file__).parent.parent

def _get_history_file():
    if os.getenv("GITHUB_ACTIONS"):
        return CHANNEL_DIR / "history.json"
    return CHANNEL_DIR / "history.local.json"

HISTORY_FILE = _get_history_file()


# ============================================
# 금융 토픽 데이터베이스 (한국어)
# ============================================
FINANCE_TOPICS = [
    # ==========================================
    # 카테고리: 금융 용어
    # ==========================================
    {
        "recipe_id": "term-pe-ratio",
        "title": "PER — 주가수익비율이 뭘까?",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/p/price-earningsratio.asp",
        "ingredients": [
            {"name": "PER", "amount": "주가 ÷ 주당순이익"},
            {"name": "낮은 PER", "amount": "15 이하 — 저평가 가능성"},
            {"name": "높은 PER", "amount": "25 이상 — 고성장 기대"},
        ],
        "steps": [
            "PER은 투자자들이 회사의 이익 1원당 얼마를 지불하는지 알려주는 지표야",
            "주가를 주당순이익(EPS)으로 나눠서 계산해",
            "PER이 15면 회사가 1원 벌 때 투자자가 15원을 내는 거야",
            "낮은 PER(15 이하)은 저평가됐거나 성장 기대가 낮다는 뜻이야",
            "높은 PER(25 이상)은 투자자들이 미래 성장을 높게 보고 있다는 뜻이야",
            "코스피 평균 PER은 역사적으로 10~12배 정도를 오가고 있어",
            "항상 같은 업종끼리 PER을 비교해야 해 다른 업종끼리는 비교하면 안 돼",
            "PER이 낮다고 무조건 좋은 건 아니야 회사에 진짜 문제가 있을 수도 있어",
        ],
    },
    {
        "recipe_id": "term-compound-interest",
        "title": "복리 — 세계 8번째 불가사의",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/c/compoundinterest.asp",
        "ingredients": [
            {"name": "복리", "amount": "이자에 이자가 붙는 것"},
            {"name": "72의 법칙", "amount": "72 ÷ 수익률 = 원금 2배 되는 해"},
            {"name": "시간", "amount": "가장 중요한 요소"},
        ],
        "steps": [
            "복리는 원금뿐 아니라 이자에도 이자가 붙는 거야",
            "아인슈타인이 세계 8번째 불가사의라고 불렀다고 해",
            "100만 원을 연 10%로 투자하면 1년 후 110만 원이 돼",
            "2년 차에는 110만 원의 10%인 11만 원이 붙어서 121만 원이 돼",
            "30년이 지나면 100만 원이 1,745만 원이 돼 한 푼도 더 안 넣어도",
            "72의 법칙으로 수익률을 72로 나누면 원금이 2배 되는 기간을 알 수 있어",
            "연 10% 수익이면 약 7.2년마다 돈이 2배가 돼",
            "10년만 일찍 시작해도 은퇴할 때 수억 원 차이가 날 수 있어",
        ],
    },
    {
        "recipe_id": "term-etf",
        "title": "ETF — 주식처럼 사고파는 펀드",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/e/etf.asp",
        "ingredients": [
            {"name": "ETF", "amount": "한 번에 여러 주식을 사는 것"},
            {"name": "코스피200 ETF", "amount": "KODEX 200, TIGER 200"},
            {"name": "보수", "amount": "연 0.05%~0.20% 수준"},
        ],
        "steps": [
            "ETF는 여러 주식을 한 바구니에 담아서 한 번에 사는 것과 같아",
            "500개 개별 주식을 살 필요 없이 ETF 하나로 다 살 수 있어",
            "ETF는 주식처럼 거래소에서 언제든 사고팔 수 있어",
            "대표적인 ETF로 KODEX 200이나 TIGER 200이 있어 코스피200을 추종해",
            "ETF는 보수라는 작은 수수료가 있는데 보통 연 0.05%에서 0.20% 사이야",
            "1,000만 원을 투자하면 연간 수수료가 5,000원에서 2만 원 정도야",
            "워렌 버핏도 대부분의 투자자에게 인덱스 ETF를 추천했어",
            "ETF로 즉시 분산투자가 되니까 개별 주식보다 위험이 낮아",
        ],
    },
    {
        "recipe_id": "term-dividend",
        "title": "배당금 — 주식 들고만 있어도 돈이 들어온다",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/d/dividend.asp",
        "ingredients": [
            {"name": "배당금", "amount": "회사가 주주에게 주는 현금"},
            {"name": "배당수익률", "amount": "연간 배당금 ÷ 주가"},
            {"name": "배당 재투자", "amount": "받은 배당으로 주식 추가 매수"},
        ],
        "steps": [
            "배당금은 회사가 번 돈의 일부를 주주에게 현금으로 나눠주는 거야",
            "주식을 들고만 있어도 매년 용돈처럼 들어오는 돈이야",
            "배당수익률이 3%인 주식에 1,000만 원 투자하면 연 30만 원이 들어와",
            "삼성전자 SK텔레콤 같은 대기업들은 매년 안정적으로 배당을 줘",
            "받은 배당금으로 다시 주식을 사면 복리 효과가 극대화돼",
            "미국의 코카콜라는 60년 넘게 배당금을 매년 올려왔어",
            "모든 회사가 배당을 주진 않아 성장 기업은 이익을 재투자하는 걸 선호해",
            "배당주는 주가 상승과 배당 수입 두 가지로 돈을 벌 수 있어",
        ],
    },
    {
        "recipe_id": "term-market-cap",
        "title": "시가총액 — 회사가 진짜 얼마짜리인지 아는 법",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/m/marketcapitalization.asp",
        "ingredients": [
            {"name": "시가총액", "amount": "주가 × 발행주식수"},
            {"name": "대형주", "amount": "시총 10조 원 이상"},
            {"name": "소형주", "amount": "시총 5,000억 원 이하"},
        ],
        "steps": [
            "시가총액은 회사의 전체 가치를 나타내는 숫자야 회사의 가격표 같은 거지",
            "주가에 발행된 주식 수를 곱하면 시가총액이 나와",
            "주가가 5만 원이고 주식이 1억 주면 시총은 5조 원이야",
            "대형주는 시총 10조 원 이상으로 삼성전자 SK하이닉스 같은 기업이야",
            "소형주는 시총 5,000억 원 이하로 위험하지만 성장 가능성이 높아",
            "주가가 1만 원인 주식이 5만 원짜리보다 비쌀 수도 있어 시총으로 비교해야 해",
            "삼성전자의 시가총액은 300조 원이 넘어 한국 1위야",
            "시총을 알면 서로 다른 회사의 크기를 공정하게 비교할 수 있어",
        ],
    },
    {
        "recipe_id": "term-dollar-cost-averaging",
        "title": "적립식 투자 — 게으른 투자자의 비밀 무기",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/d/dollarcostaveraging.asp",
        "ingredients": [
            {"name": "적립식 투자", "amount": "매월 정해진 금액을 자동 투자"},
            {"name": "장점", "amount": "감정을 배제한 투자"},
            {"name": "예시", "amount": "매월 10만 원 자동 매수"},
        ],
        "steps": [
            "적립식 투자는 매월 정해진 금액을 자동으로 투자하는 방법이야",
            "타이밍을 잡으려 하지 말고 매달 꾸준히 같은 금액을 넣으면 돼",
            "비싸면 적게 사고 싸면 많이 사게 되니까 평균 매입가가 낮아져",
            "결과적으로 잘못된 타이밍에 한꺼번에 사는 위험이 줄어들어",
            "매달 10만 원씩 코스피200 ETF에 넣으면 1년에 120만 원이 모여",
            "핵심은 꾸준함이야 시장이 올라도 내려도 계속 투자하는 거지",
            "자동이체를 설정하면 의지력 없이도 적립식 투자가 되니까",
            "자동이체 한 번 설정해두면 자는 동안에도 투자가 알아서 돌아가",
        ],
    },
    {
        "recipe_id": "term-bull-bear-market",
        "title": "상승장 vs 하락장 — 어떤 차이가 있을까?",
        "category": "finance-terms",
        "url": "https://www.investopedia.com/terms/b/bullmarket.asp",
        "ingredients": [
            {"name": "상승장(Bull)", "amount": "저점에서 20% 이상 상승"},
            {"name": "하락장(Bear)", "amount": "고점에서 20% 이상 하락"},
            {"name": "평균 상승장", "amount": "약 5년 지속"},
        ],
        "steps": [
            "상승장은 주가가 올라가거나 올라갈 것으로 예상되는 시장이야 황소가 뿔을 들어올리는 모습에서 왔어",
            "하락장은 주가가 최고점에서 20% 이상 떨어진 시장이야 곰이 앞발을 내리치는 모습이지",
            "평균적으로 상승장은 약 5년 하락장은 약 1년 정도 지속돼",
            "1945년 이후 12번의 하락장이 있었는데 매번 그 뒤에 새로운 최고점을 찍었어",
            "2020년 코로나 때 코스피가 38% 폭락했어 역대 가장 빠른 하락장이었지",
            "그런데 불과 11개월 만에 모든 손실을 회복하고 사상 최고치를 찍었어",
            "핵심 교훈은 하락장은 일시적이고 상승장이 장기적인 추세라는 거야",
            "가장 많이 잃는 투자자는 하락장에서 공포에 팔아버리는 사람이야",
        ],
    },
    # ==========================================
    # 카테고리: 투자 기초
    # ==========================================
    {
        "recipe_id": "invest-rule-of-72",
        "title": "72의 법칙 — 내 돈이 얼마나 빨리 2배 될까?",
        "category": "investment-basics",
        "url": "https://www.investopedia.com/terms/r/ruleof72.asp",
        "ingredients": [
            {"name": "72의 법칙", "amount": "72 ÷ 연 수익률 = 2배 되는 햇수"},
            {"name": "6% 수익", "amount": "12년에 2배"},
            {"name": "10% 수익", "amount": "7.2년에 2배"},
        ],
        "steps": [
            "72의 법칙은 돈이 2배가 되려면 얼마나 걸리는지 머릿속으로 바로 계산하는 방법이야",
            "72를 연간 수익률로 나누면 원금이 2배 되는 햇수가 나와",
            "연 6%면 12년 후에 2배가 돼 (72 ÷ 6 = 12)",
            "연 10%면 약 7.2년 후에 2배 (72 ÷ 10 = 7.2)",
            "은행 금리 1%면 72년이 걸려 사실상 평생이야",
            "주식 시장의 역사적 평균인 10%면 약 7년마다 2배야",
            "이래서 수익률 몇 퍼센트 차이가 장기적으로 어마어마한 차이를 만들어",
            "25살에 시작하면 35살에 시작하는 것보다 한 번 더 2배가 돼 은퇴할 때 2배 차이야",
        ],
    },
    {
        "recipe_id": "invest-index-funds",
        "title": "인덱스 펀드 — 전문가 90%가 이기지 못하는 투자법",
        "category": "investment-basics",
        "url": "https://www.investopedia.com/terms/i/indexfund.asp",
        "ingredients": [
            {"name": "인덱스 펀드", "amount": "시장 지수를 그대로 따라가는 펀드"},
            {"name": "코스피200", "amount": "한국 상위 200개 기업"},
            {"name": "보수", "amount": "연 0.03%~0.20%로 매우 저렴"},
        ],
        "steps": [
            "인덱스 펀드는 코스피200 같은 시장 지수를 자동으로 따라가는 펀드야",
            "펀드매니저가 종목을 고르는 게 아니라 지수에 있는 모든 종목을 그냥 사는 거야",
            "액티브 펀드의 90% 이상이 15년 동안 시장 지수를 이기지 못했어",
            "워렌 버핏은 100만 달러를 걸고 인덱스 펀드가 헤지펀드를 이긴다고 했고 실제로 이겼어",
            "인덱스 펀드 보수는 0.03%~0.20%로 액티브 펀드의 1~2%보다 훨씬 저렴해",
            "1,000만 원을 30년 투자하면 수수료 차이만 2,000만 원 이상이야",
            "1976년에 존 보글이 최초의 인덱스 펀드를 만들었을 때 사람들이 바보짓이라 했어",
            "지금 인덱스 펀드에 들어있는 돈이 1경 원이 넘어 농담에서 가장 똑똑한 투자법이 됐어",
        ],
    },
    {
        "recipe_id": "invest-diversification",
        "title": "분산투자 — 달걀을 한 바구니에 담지 마라",
        "category": "investment-basics",
        "url": "https://www.investopedia.com/terms/d/diversification.asp",
        "ingredients": [
            {"name": "분산투자", "amount": "여러 자산에 나눠 투자"},
            {"name": "자산 종류", "amount": "주식, 채권, 부동산"},
            {"name": "위험 감소", "amount": "변동성 낮추고 안정적 수익"},
        ],
        "steps": [
            "분산투자는 돈을 여러 투자처에 나눠서 위험을 줄이는 거야",
            "한 종목에 올인했는데 그 회사가 망하면 전 재산을 잃게 되지",
            "하지만 500개 종목을 갖고 있으면 하나가 망해도 포트폴리오에 거의 영향이 없어",
            "자산 종류별로 업종별로 나라별로 기업 크기별로 나눌 수 있어",
            "간단한 분산 포트폴리오는 국내 주식 해외 주식 채권으로 구성할 수 있어",
            "2008년 금융위기 때 주식이 폭락하면서 채권은 올랐어 이게 분산투자의 힘이야",
            "가장 쉬운 분산투자 방법은 전체 시장 인덱스 펀드를 사는 거야",
            "분산투자는 최고 수익을 주진 않지만 최악의 손실로부터 지켜줘",
        ],
    },
    {
        "recipe_id": "invest-emergency-fund",
        "title": "비상금 — 당신의 재정 안전망",
        "category": "investment-basics",
        "url": "https://www.investopedia.com/terms/e/emergency_fund.asp",
        "ingredients": [
            {"name": "비상금", "amount": "생활비 3~6개월분 저축"},
            {"name": "보관 장소", "amount": "CMA 또는 고금리 예금"},
            {"name": "목적", "amount": "예상치 못한 지출 대비"},
        ],
        "steps": [
            "비상금은 갑자기 직장을 잃거나 병원비가 나올 때를 위한 돈이야",
            "재정 전문가들은 투자를 시작하기 전에 생활비 3~6개월분을 먼저 모으라고 해",
            "비상금이 없으면 급할 때 투자를 손해 보고 팔아야 할 수도 있어",
            "한국 직장인 59%가 갑자기 100만 원 쓸 일이 생기면 감당 못 한다고 답했어",
            "처음엔 50만 원부터 시작해도 돼 대부분의 긴급 상황을 커버할 수 있어",
            "비상금은 CMA나 고금리 파킹통장에 넣어두면 연 3~4% 이자를 받을 수 있어",
            "일반 은행 보통예금 금리는 0.1%인데 고금리 통장은 30배 이상 줘",
            "비상금은 나 자신을 위한 보험이야 재정적 재난이 인생을 망치지 않게 해줘",
        ],
    },
    # ==========================================
    # 카테고리: 주식 시장
    # ==========================================
    {
        "recipe_id": "stock-kospi",
        "title": "코스피 — 한국 주식시장의 기준점",
        "category": "stock-market",
        "url": "https://finance.yahoo.com/quote/%5EKS11/",
        "ingredients": [
            {"name": "코스피", "amount": "한국 유가증권시장 종합지수"},
            {"name": "연평균 수익률", "amount": "약 7~8% (배당 포함)"},
            {"name": "대표 종목", "amount": "삼성전자, SK하이닉스, LG에너지솔루션"},
        ],
        "steps": [
            "코스피는 한국 유가증권시장에 상장된 모든 기업의 주가를 종합한 지수야",
            "뉴스에서 오늘 주식시장 올랐다 내렸다 할 때 보통 코스피를 말하는 거야",
            "삼성전자 SK하이닉스 LG에너지솔루션 같은 대기업이 포함돼 있어",
            "1980년 100포인트에서 시작해서 현재 2,500포인트 이상까지 올랐어",
            "코스피에 투자하면 연평균 7~8%의 수익률을 기대할 수 있어 배당 포함",
            "시총 가중 방식이라 삼성전자 같은 큰 회사가 지수에 큰 영향을 줘",
            "코스피를 직접 살 순 없지만 KODEX 200이나 TIGER 200 ETF로 투자할 수 있어",
            "코스피에 투자하는 건 한국 경제 전체의 성장에 베팅하는 거야",
        ],
    },
    {
        "recipe_id": "stock-what-is-stock",
        "title": "주식이 뭘까? — 회사의 주인이 되는 법",
        "category": "stock-market",
        "url": "https://www.investopedia.com/terms/s/stock.asp",
        "ingredients": [
            {"name": "주식", "amount": "회사 소유권의 한 조각"},
            {"name": "거래소", "amount": "한국거래소 (KRX)"},
            {"name": "종목 코드", "amount": "삼성전자 005930, 카카오 035720"},
        ],
        "steps": [
            "주식은 회사의 아주 작은 소유권 한 조각이야",
            "삼성전자 주식 1주를 사면 너도 삼성전자의 주인 중 한 명이 되는 거야",
            "회사는 성장에 필요한 돈을 모으기 위해 주식을 팔고 투자자는 가치 상승을 기대하고 사",
            "주식은 한국거래소에서 주식시장 열리는 시간에 사고팔 수 있어",
            "모든 주식에는 종목 코드가 있어 삼성전자는 005930 카카오는 035720이야",
            "사려는 사람이 많으면 주가가 오르고 팔려는 사람이 많으면 내려가",
            "주주로서 돈 버는 방법은 두 가지야 주가 상승 또는 배당금 수령",
            "수천만 원이 필요한 게 아냐 요즘은 소수점 주식으로 1만 원부터 투자할 수 있어",
        ],
    },
    {
        "recipe_id": "stock-ipo",
        "title": "IPO — 비공개 회사가 주식시장에 데뷔하는 날",
        "category": "stock-market",
        "url": "https://www.investopedia.com/terms/i/ipo.asp",
        "ingredients": [
            {"name": "IPO", "amount": "기업공개, 최초 주식 상장"},
            {"name": "상장", "amount": "일반 투자자가 주식을 살 수 있게 됨"},
            {"name": "보호예수", "amount": "내부자 90~180일간 매도 제한"},
        ],
        "steps": [
            "IPO는 비공개 회사가 처음으로 주식시장에 상장하는 거야",
            "IPO 전에는 창업자 직원 초기 투자자만 회사를 소유할 수 있어",
            "회사는 사업 확장 자금을 마련하려고 주식시장에 상장해",
            "카카오뱅크 IPO 때 공모가의 2배 넘게 올라서 따상이라는 말이 유행했어",
            "상장 첫날 주가가 크게 오르는 경우가 많아 흥행하는 것처럼 보이지",
            "하지만 연구에 따르면 대부분의 IPO 종목은 3년 후 시장 평균보다 수익률이 낮아",
            "내부자는 보호예수 기간 90일에서 180일 동안 주식을 팔 수 없어",
            "초보자라면 IPO 열기가 식은 후에 사는 게 더 안전해",
        ],
    },
    # ==========================================
    # 카테고리: 재테크 팁
    # ==========================================
    {
        "recipe_id": "tip-50-30-20-rule",
        "title": "50/30/20 법칙 — 세상에서 가장 쉬운 가계부",
        "category": "personal-finance",
        "url": "https://www.investopedia.com/ask/answers/022916/what-502030-budget-rule.asp",
        "ingredients": [
            {"name": "50% 필수", "amount": "월세, 식비, 공과금, 보험"},
            {"name": "30% 원하는 것", "amount": "외식, 취미, 구독 서비스"},
            {"name": "20% 저축", "amount": "투자, 비상금, 빚 상환"},
        ],
        "steps": [
            "50/30/20 법칙은 세금 뗀 월급을 세 가지로 나누는 초간단 가계부야",
            "50%는 필수 지출이야 월세 식비 교통비 보험 최소 빚 상환",
            "30%는 원하는 것에 써 외식 구독 서비스 취미 쇼핑",
            "20%는 저축과 투자야 비상금 투자 추가 빚 상환",
            "월급이 300만 원이면 150만 원 필수 90만 원 생활 60만 원 저축이야",
            "앨리자베스 워런 상원의원이 자신의 책에서 이 법칙을 대중화시켰어",
            "좋은 점은 매일 지출을 기록할 필요가 없다는 거야 큰 틀만 지키면 돼",
            "처음부터 20%가 힘들면 10%부터 시작해도 괜찮아 안 하는 것보다 백배 나아",
        ],
    },
    {
        "recipe_id": "tip-pay-yourself-first",
        "title": "선저축 후소비 — 부자들이 아는 비밀",
        "category": "personal-finance",
        "url": "https://www.investopedia.com/terms/p/payyourselffirst.asp",
        "ingredients": [
            {"name": "선저축 후소비", "amount": "쓰기 전에 먼저 저축"},
            {"name": "자동이체", "amount": "월급날 자동 저축 설정"},
            {"name": "파킨슨 법칙", "amount": "돈이 있으면 있는 만큼 쓰게 됨"},
        ],
        "steps": [
            "선저축 후소비는 돈을 쓰기 전에 먼저 저축이나 투자를 하는 거야",
            "보통 사람들은 다 쓰고 남은 돈을 저축하는데 남는 돈이 없어",
            "부자들은 반대로 해 먼저 저축하고 남은 돈으로 생활해",
            "이게 되는 이유는 파킨슨 법칙 때문이야 돈이 있으면 있는 만큼 쓰게 되거든",
            "월급 300만 원에서 30만 원을 먼저 빼면 270만 원으로 생활하게 돼",
            "월급날 자동이체로 저축 통장이나 투자 계좌에 돈이 빠지게 설정해",
            "월급의 5%부터 시작해도 수십 년이면 엄청난 차이를 만들어",
            "가장 좋은 점은 자동화하면 의지력이 필요 없다는 거야",
        ],
    },
    {
        "recipe_id": "tip-credit-score",
        "title": "신용점수 — 당신의 금융 인생을 지배하는 숫자",
        "category": "personal-finance",
        "url": "https://www.investopedia.com/terms/c/credit_score.asp",
        "ingredients": [
            {"name": "신용점수", "amount": "1~1000점 (NICE 기준)"},
            {"name": "좋은 점수", "amount": "900점 이상이면 최우량"},
            {"name": "상환 이력", "amount": "점수에 가장 큰 영향"},
        ],
        "steps": [
            "신용점수는 금융기관이 너를 얼마나 신뢰하는지 보여주는 숫자야",
            "높은 점수면 대출 금리가 낮아지고 카드 한도도 올라가",
            "신용점수 700점과 900점의 차이로 주택 담보 대출 이자가 수천만 원 차이 날 수 있어",
            "가장 중요한 건 제때 갚는 거야 한 번만 연체해도 점수가 크게 떨어져",
            "카드 사용 비율도 중요해 한도의 30% 이하로 유지하는 게 좋아",
            "오래된 카드는 해지하지 마 신용 이력이 길수록 점수에 유리해",
            "토스나 카카오페이에서 무료로 신용점수를 확인할 수 있어",
            "젊을 때 신용을 잘 관리하는 게 인생에서 가장 똑똑한 금융 결정 중 하나야",
        ],
    },
    # ==========================================
    # 카테고리: 역사적 수익
    # ==========================================
    {
        "recipe_id": "history-samsung-100",
        "title": "10년 전 삼성전자에 100만 원 넣었다면?",
        "category": "historical-returns",
        "url": "https://finance.yahoo.com/quote/005930.KS/",
        "ingredients": [
            {"name": "삼성전자 (005930)", "amount": "2014년에 100만 원 투자"},
            {"name": "수익", "amount": "약 150만~200만 원 (배당 포함)"},
            {"name": "배당", "amount": "매년 꾸준한 배당 수입"},
        ],
        "steps": [
            "10년 전 삼성전자에 100만 원을 투자했다면 지금 약 150만~200만 원이 됐을 거야",
            "주가 상승분에 매년 받은 배당금까지 더하면 수익이 더 올라가",
            "삼성전자는 반도체 스마트폰으로 꾸준히 실적을 만들어 왔어",
            "배당금을 다시 주식에 넣었다면 복리 효과로 수익이 더 컸을 거야",
            "매달 10만 원씩 적립식으로 투자했다면 목돈보다 수익률이 더 좋았을 수 있어",
            "하지만 과거 수익이 미래를 보장하지는 않아 반도체 사이클에 따라 변동이 커",
            "중요한 건 좋은 기업에 투자하고 오래 들고 있는 거야",
            "교훈은 큰돈이 아니라 시간이 진짜 자산이라는 거야",
        ],
    },
    {
        "recipe_id": "history-kospi-100",
        "title": "20년 전 코스피에 100만 원 넣었다면?",
        "category": "historical-returns",
        "url": "https://finance.yahoo.com/quote/%5EKS11/",
        "ingredients": [
            {"name": "코스피 지수", "amount": "2004년에 100만 원 투자"},
            {"name": "수익", "amount": "약 300만~400만 원"},
            {"name": "겪은 위기", "amount": "2008년 금융위기, 2020년 코로나"},
        ],
        "steps": [
            "20년 전 코스피 인덱스 펀드에 100만 원을 넣었다면 지금 약 300만~400만 원이야",
            "그 사이 2008년 금융위기를 거쳤어 코스피가 50% 넘게 폭락했지",
            "2020년 코로나 때도 38%가 빠졌어 공포 그 자체였어",
            "하지만 장기적으로 보면 항상 다시 올라왔어",
            "공포에 팔아버린 투자자들은 회복을 놓치고 돈을 잃었어",
            "꾹 참고 들고 있었던 투자자들은 원금 회복은 물론 신고가를 찍었어",
            "시장에서 시간을 보내는 게 타이밍을 잡는 것보다 중요하다는 거야",
            "매달 10만 원씩 30년 적립식으로 넣었다면 1억 원 이상이 됐을 거야",
        ],
    },
    {
        "recipe_id": "history-bitcoin-100",
        "title": "2015년에 비트코인에 100만 원 넣었다면?",
        "category": "historical-returns",
        "url": "https://finance.yahoo.com/quote/BTC-KRW/",
        "ingredients": [
            {"name": "비트코인 (BTC)", "amount": "2015년 1월에 100만 원 투자"},
            {"name": "당시 가격", "amount": "개당 약 25만 원"},
            {"name": "극심한 변동성", "amount": "50% 이상 폭락 최소 5회"},
        ],
        "steps": [
            "2015년 1월에 비트코인이 약 25만 원일 때 100만 원을 넣었다면 약 4개를 샀을 거야",
            "비트코인 최고가 기준으로 그 4개가 수억 원 이상 가치가 됐을 거야",
            "하지만 그 과정이 절대 순탄하지 않았어 50% 이상 폭락이 최소 다섯 번 있었어",
            "2018년에는 2,500만 원에서 400만 원까지 떨어졌어 85% 폭락이야",
            "대부분의 사람들은 폭락 때 팔아서 실제로는 손해를 봤어",
            "끝까지 들고 있을 수 있었던 건 극한의 인내심과 리스크 감수 능력이 있는 사람뿐이야",
            "비트코인은 초고위험 초고수익 자산이야 잃어도 괜찮은 돈만 넣어야 해",
            "교훈은 비트코인을 사라가 아니라 엄청난 수익에는 엄청난 인내와 리스크가 따른다는 거야",
        ],
    },
]


class RecipeCrawler:
    """
    Money Bite 금융 토픽 크롤러
    파이프라인 호환을 위해 RecipeCrawler 이름 유지
    """
    
    def __init__(self):
        self.topics = FINANCE_TOPICS
        logger.info(f"FinanceCrawler initialized with {len(self.topics)} topics")
    
    def _load_history(self) -> dict:
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {"used_recipes": [], "last_category_index": 0}
        return {"used_recipes": [], "last_category_index": 0}
    
    def _save_history(self, history: dict):
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def mark_as_used(self, recipe_id: str, title: str, category: str = "finance", url: str = None):
        history = self._load_history()
        history["used_recipes"].append({
            "recipe_id": recipe_id,
            "title": title,
            "category": category,
            "url": url or "",
            "used_at": datetime.now().isoformat()
        })
        self._save_history(history)
        logger.info(f"Marked as used: {recipe_id} - {title}")
    
    def get_used_recipe_ids(self) -> list:
        history = self._load_history()
        return [r["recipe_id"] for r in history.get("used_recipes", [])]
    
    def get_next_recipe(self) -> dict:
        used_ids = set(self.get_used_recipe_ids())
        
        categories = [
            "finance-terms",
            "investment-basics",
            "stock-market",
            "personal-finance",
            "historical-returns",
        ]
        
        history = self._load_history()
        last_cat_idx = history.get("last_category_index", 0)
        
        for offset in range(len(categories)):
            cat_idx = (last_cat_idx + offset) % len(categories)
            category = categories[cat_idx]
            
            available = [
                t for t in self.topics 
                if t["category"] == category and t["recipe_id"] not in used_ids
            ]
            
            if available:
                topic = random.choice(available)
                
                history["last_category_index"] = (cat_idx + 1) % len(categories)
                self._save_history(history)
                
                logger.info(f"Selected topic: [{topic['category']}] {topic['title']}")
                
                steps_as_dicts = [
                    {"step_number": i + 1, "description": step}
                    for i, step in enumerate(topic["steps"])
                ]
                
                return {
                    "recipe_id": topic["recipe_id"],
                    "title": topic["title"],
                    "steps": steps_as_dicts,
                    "ingredients": topic.get("ingredients", []),
                    "category": topic["category"],
                    "url": topic.get("url", ""),
                }
        
        logger.warning("All topics have been used!")
        print("⚠️  모든 금융 토픽이 사용되었습니다. 토픽을 추가해주세요.")
        return None


if __name__ == "__main__":
    crawler = RecipeCrawler()
    topic = crawler.get_next_recipe()
    if topic:
        print(f"\n=== 선택된 토픽 ===")
        print(f"제목: {topic['title']}")
        print(f"카테고리: {topic['category']}")
        print(f"핵심 개념: {', '.join([i['name'] for i in topic['ingredients']])}")
        print(f"교육 포인트: {len(topic['steps'])}개")
        print(f"\n내용:")
        for step in topic['steps']:
            print(f"  {step['step_number']}. {step['description']}")
    else:
        print("사용 가능한 토픽이 없습니다.")
