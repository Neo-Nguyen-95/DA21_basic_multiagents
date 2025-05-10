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
       
        
user_message = "Tôi nhận được lương 15 triệu vào ngày 02/05/2025"

note_taker = NoteTakingAgent()
data = note_taker.run(user_message)

#%% II. DataSaverAgent




#%% III. VisualizerAgent




#%% Multi-agent Activation 



