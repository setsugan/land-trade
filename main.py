import requests
from bs4 import BeautifulSoup
import yfinance as yf

# Constants
LOGIN_URL = 'https://www.ssg.ne.jp/session'
ORDER_URL = 'https://www.ssg.ne.jp/orders/bulk'
LOGIN_SUCCESS_TEXT = (
    '<a class="el_btn el_btn__small el_btn__greenVer2 logoutBtn_sp" '
    'href="/logout" data-turbolinks="false">ログアウト</a>'
)
STOCK_DATA_URL = 'https://www.ssg.ne.jp/performances/team'

# Login data
LOGIN_DATA = {
    'course_code': "57226",
    'course_password': "480362",
    'user_code': "0307",
    'user_password': "577163",
    'button': ''
}

# Order data
ORDER_DATA = {'limit': ''}
for i in range(1, 11):
    ORDER_DATA.update({
        f'order_{i:02}[ticker_symbol]': '',
        f'order_{i:02}[volume]': '',
        f'order_{i:02}[selling]': 'null'
    })

def login(session: requests.Session, url: str, data: dict) -> bool:
    """Attempt to log in and return True if successful."""
    response = session.post(url, data=data)
    if LOGIN_SUCCESS_TEXT in response.text:
        print("Login successful")
        return True
    else:
        print("Login failed")
        return False

def send_order(session: requests.Session, url: str, data: dict) -> None:
    """Send an order."""
    response = session.post(url, data=data)
    if response.status_code == 200:
        print("Order sent successfully")
    else:
        print("Order sending failed")

def get_stock_data(session: requests.Session) -> tuple[bool, list]:
    """Retrieve stock holdings and return the data if available."""
    response = session.get(STOCK_DATA_URL)
    soup = BeautifulSoup(response.text, 'html.parser')
    divs = soup.find_all('div', class_='table_wrapper')
    
    if len(divs) < 2:
        print("Second div not found")
        return False, []
    
    second_div = divs[1]
    table = second_div.find('table', class_='Dealings sp_layout')
    rows = table.find_all('tr')[1:]  # Skip header row
    
    data = [
        [col.text.strip().replace(',', '') for col in row.find_all('td')]
        for row in rows
    ]
    
    return bool(data), data

def get_total_assets(session: requests.Session) -> int | None:
    """Retrieve total assets and return None if not found."""
    response = session.get('https://www.ssg.ne.jp/performances/team')
    soup = BeautifulSoup(response.text, 'html.parser')
    temo_stock_div = soup.find('div', id='temoStock')
    if temo_stock_div:
        table = temo_stock_div.find('table')
        if table:
            tbody = table.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                if len(rows) >= 2:
                    second_row = rows[1]
                    cols = second_row.find_all('td')
                    if cols:
                        total_assets = cols[0].text.strip().replace(',', '')
                        return int(total_assets)
    print("Total assets not found")
    return None

def get_land_stock_prices() -> tuple[float, float] | None:
    """Retrieve the closing and low prices of Land's stock, or return None if not found."""
    stock = yf.Ticker("8918.T")  # Land stock code
    hist = stock.history(period="1d")
    if not hist.empty:
        close_price = hist['Close'].iloc[0]
        low_price = hist['Low'].iloc[0]
        return close_price, low_price
    else:
        print("Land stock prices not found")
        return None

def main() -> None:
    """Main function to execute the trading logic."""
    session = requests.Session()
    if login(session, LOGIN_URL, LOGIN_DATA):
        has_stock, stock_data = get_stock_data(session)
        stock_prices = get_land_stock_prices()
        if stock_prices:
            close_price, low_price = stock_prices
            if has_stock and close_price > low_price:
                ORDER_DATA['order_01[ticker_symbol]'] = '8918'
                ORDER_DATA['order_01[volume]'] = stock_data[0][2]
                ORDER_DATA['order_01[selling]'] = 'true'
                print("Selling Land stock")
            elif not has_stock and close_price == low_price:
                total_assets = int(get_total_assets(session))
                num_shares = total_assets // (low_price * 100)
                print(f"Number of Land shares to buy: {num_shares * 100} shares")
                ORDER_DATA['order_01[ticker_symbol]'] = '8918'
                ORDER_DATA['order_01[volume]'] = str(num_shares * 100)[:-2]
                ORDER_DATA['order_01[selling]'] = 'false'
                print("Buying Land stock")
            else:
                print("Order conditions not met, no order sent")
                return
            send_order(session, ORDER_URL, ORDER_DATA)
        else:
            print("Stock price data not found, terminating")

if __name__ == "__main__":
    main()
