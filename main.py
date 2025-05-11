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
import matplotlib.pyplot as plt

#%% I. NoteTakingAgent

class NoteTakingAgent:
    def run(self, user_message):
        client = OpenAI(api_key = api_key)
        
        dev_message = f"""
        Bạn là một người quản lí chi tiêu người Việt Nam. 
        Đơn vị tiền của Việt Nam là VND. Người Việt Nam thường viết tắt nhìn bằng k, 
        ví dụ 100k là 100000 VND, 15k là 15000 VND.
        Cho kết quả là ở định dạng  json như sau:
         {{
             "date": ngày chi tiêu (sử dụng {datetime.now().date().isoformat()} nếu không đề cập)
             người Việt thường viết ngày/tháng/năm nên cần đổi sang dạng năm-tháng-ngày,
             "amount": số tiền,
             "unit": đơn vị tiền (mặc định là VND),
             "flow": income hoặc expense,
             "purpose": một trong các loại sau:
                 Necessities (thức ăn, nơi ở, phương tiện đi lại, tiện ích, điện, , ...), 
                 Saving (cổ phiếu, quỹ tương hỗ, bất động sản, ...), 
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
       
        
user_message = "du lịch hết 1tr"

note_taker = NoteTakingAgent()
data = note_taker.run(user_message)

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
                           purpose TEXT
                           )
                       """)
        try:
            cursor.execute("""
                           INSERT INTO personal_fin_data(date, amount, unit, flow, purpose)
                           VALUES (?, ?, ?, ?, ?)
                           """,(
                           data['date'],
                           data['amount'],
                           data['unit'],
                           data['flow'],
                           data['purpose']
                           ))
        except Exception as e:
            print("Insert fail because: ", e)
            
        conn.commit()
        conn.close()

data_saver = DataSaverAgent()
data_saver.run(data)

# Check after load
conn = sqlite3.connect("database.db")
sql = "SELECT * FROM personal_fin_data"
data = pd.read_sql(sql=sql, con=conn)
print(data)

#%% III. VisualizerAgent

total_income = data.groupby('flow')['amount'].sum()['income']
total_expense = data.groupby('flow')['amount'].sum()['expense']
tota_remain = total_income - total_expense
data_remain = pd.DataFrame({
    "date": [datetime.now().date().isoformat()],
    "amount": [tota_remain],
    "unit": ["VND"],
    "flow": ["remain"],
    "purpose": ["Remain"]
    })

data = pd.concat([data, data_remain], axis="rows")
data.reset_index(inplace=True, drop=True)

# Expense pie chart
data_pie = (data[data['flow'] != 'income']
            .groupby('purpose')['amount'].sum()
            )

plt.pie(x=data_pie.values, labels=data_pie.index, autopct='%1.1f%%')
plt.show()
#%% Multi-agent Activation 



