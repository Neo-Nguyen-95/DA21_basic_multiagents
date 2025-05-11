"""
MULTI-AGENTS WORKFLOW

NoteTakingAgent -> DataSaverAgent -> VisualizerAgent

"""

#%% LIB
from dotenv import load_dotenv
import os
load_dotenv()
from openai import OpenAI
api_key = os.getenv("SECRETE_KEY")

import json
from datetime import datetime
import sqlite3
import pandas as pd
pd.set_option("display.max_columns", None)
import matplotlib.pyplot as plt
import seaborn as sns
import time

#%% I. NoteTakingAgent

class NoteTakingAgent:
    def run(self, user_message):
        client = OpenAI(api_key = api_key)
        
        dev_message = f"""
        Bạn là một người quản lí chi tiêu người Việt Nam. 
        Đơn vị tiền của Việt Nam là VND. Người Việt Nam thường viết tắt nhìn bằng k, 
        ví dụ 100k là 100000 VND, 15k là 15000 VND.
        Từ dữ liệu nhận được, hãy phân tích chi tiêu qua các bước:
            1. Đây là hoạt động gì?
            2. Phục vụ cho nhu cầu gì?
            3. Viết lại ghi chú lại kết quả ở dạng json như sau: 
         {{
             "note": trình bày diễn giải về hoạt động, hoạt động gì?, phục vụ nhu cầu gì?
             "date": ngày chi tiêu (sử dụng {datetime.now().date().isoformat()} nếu không đề cập)
             người Việt thường viết ngày/tháng/năm nên cần đổi sang dạng năm-tháng-ngày,
             "amount": số tiền,
             "unit": đơn vị tiền (mặc định là VND),
             "flow": income hoặc expense,
             "purpose": một trong các loại sau:
                 Necessities (thức ăn, nơi ở, phương tiện đi lại, tiện ích, điện, , ...), 
                 Saving (mua cổ phiếu, mua chứng chỉ quỹ tương hỗ, mua bất động sản, 
                         mua vàng, mở tài khoản tiết kiệm...), 
                 Play (bữa tối sang trọng, ngày đi spa, du lịch, hòa nhạc.), 
                 Give (các tổ chức phi lợi nhuận, các nhóm tôn giáo, các tổ chức phi chính phủ, những người liên lạc cá nhân có nhu cầu.), 
                 Education (sách, khóa học, huấn luyện, cố vấn.),
                 Salary (nếu số tiền nhận được là lương),
                 Others (nếu không thuộc các loại trên)
             }}
        """

        prompt = client.chat.completions.create(
            model='gpt-4.1-nano',
            messages=[
                {
                    "role": "developer",
                    "content": dev_message
                    },
                {
                    "role": "user",
                    "content": user_message
                    }
                ]
            )
        
        response = prompt.choices[0].message.content
        
        return json.loads(response)
       
        
#%% II. DataSaverAgent

class DataSaverAgent:
    def run(self, data):
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS personal_fin_data(
                           date TEXT,
                           amount INT,
                           unit TEXT,
                           flow TEXT,
                           purpose TEXT,
                           note TEXT
                           )
                       """)
        try:
            cursor.execute("""
                           INSERT INTO personal_fin_data(date, amount, unit, flow, purpose, note)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """,(
                           data['date'],
                           data['amount'],
                           data['unit'],
                           data['flow'],
                           data['purpose'],
                           data['note']
                           ))
        except Exception as e:
            print("Insert fail because: ", e)
            
        conn.commit()
        
        sql = "SELECT * FROM personal_fin_data"
        data = pd.read_sql(sql=sql, con=conn)
        
        data.to_csv('export_table.csv')
        
        conn.close()
        
        return data
    
#%% III. VisualizerAgent

class VisualizingAgent:
    def run(self, data):
        total_income = data.groupby('flow')['amount'].sum()['income']
        try:
            total_expense = data.groupby('flow')['amount'].sum()['expense']
        except:
            total_expense = 0
        tota_remain = total_income - total_expense
        data_remain = pd.DataFrame({
            "date": [datetime.now().date().isoformat()],
            "amount": [tota_remain],
            "unit": ["VND"],
            "flow": ["remain"],
            "purpose": ["Remain"],
            "note": ["remain"]
            })
        
        data = pd.concat([data, data_remain], axis="rows")
        data.reset_index(inplace=True, drop=True)
        
        # Pie chart
        data_pie = (data[data['flow'] != 'income']
                    .groupby('purpose')['amount'].sum()
                    .sort_values(ascending=False)
                    )
        
        fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(12, 3))
        ax[0].pie(x=data_pie.values, labels=data_pie.index, autopct='%1.1f%%',
                  pctdistance=1.2, labeldistance=1.5)
        ax[0].set_title('Overall spending and remaining')
        
        # Bar chart
        data_bar = (data_pie.reset_index())
        data_bar = data_bar[data_bar['purpose'] != 'Remain']
        
        ax_sns = sns.barplot(data=data_bar, y='amount', x='purpose', 
                             ax=ax[1])
        try:
            ax[1].bar_label(ax_sns.containers[0])
        except:
            pass
        ax[1].set_title('Amount of spending')
        ax[1].set_xlabel('Purpose')
        ax[1].set_ylabel('Amount [VND]')
        
        plt.show()

#%% Multi-agent Activation 

def main(user_message):
    agents = [NoteTakingAgent(), DataSaverAgent(), VisualizingAgent()]
    
    data = user_message
    
    for agent in agents:
        data = agent.run(data)
        print(data)

mess_chain = [
    "1/5 nhận lương 30 triệu",
    "1/5 tiết kiệm 5 triệu",
    "2/5 mua cổ phiếu 2tr2",
    "1/5 đi mua sách cho em bé hết 120k",
    "ăn sáng 2/5 40k",
    "trưa đi ăn với đồng nghiệp 99k ngày 3/5",
    "4/5 quyên góp 500k cho mặt trận tổ quốc", 
    "8/5 đi concert anh trai vượt ngàn anh hai hết 1tr8, mua thêm sticker, tổng hết 2tr",
    "9/5 đi siêu thị hết 708k",
    "10/5 đi ăn pizza 4P đẳng sờ cấp hết 990000",
    "cho con đi nhà bóng hết 121k",
    "sửa cửa hết 2 triệu",
    "note cho ngày 7/5 cắt kính cận bóng đá hết 451k",
    "đi đường rơi mất 5k do bất cẩn",
    "1tr8 đăng kí khoá học data science online 8/5",
    "bị vợ trấn lột mất 300k"
    ]

for user_message in mess_chain:
    main(user_message)
    time.sleep(2)
