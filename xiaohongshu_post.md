# 小红书文案

---

**标题：** 🇸🇬在新加坡租condo？这个开源工具帮你省时省力

---

在坡租房的朋友们，是不是每次找condo都要在99.co、PropertyGuru、URA之间来回切换，一个一个查历史租金，累到怀疑人生？

分享一个自己做的小工具 **SG Condo Rental Search**，把这些步骤自动化了👇

**它能做什么：**
📊 自动拉取URA官方租金数据（551个condo项目）
🗺️ 地图上直接看condo位置和MRT的距离
💰 显示每个condo的租金中位数和P25-P75区间
🔗 一键跳转99.co/PropertyGuru看在租房源
🔍 支持中英文自然语言搜索

**怎么用：**
打开网页，输入比如：
- "Queenstown 1b1b 3300"
- "找Bishan附近2房4000以内"

就会帮你筛选出符合条件的所有condo，按价格排序，还能在地图上一目了然。

**砍价小技巧：**
工具里会显示每个condo的P25（25分位租金），这个就是你砍价的目标价。拿着URA的历史数据去跟中介谈，比空口砍价有底气多了。

**完全免费开源：**
GitHub: github.com/demoleiwang/SGCondoRentalSearch

```
pip install -r requirements.txt
streamlit run app.py
```

三行命令就能跑起来。

---

如果对你有帮助，欢迎star⭐支持一下～也欢迎提issue或者PR，一起完善这个工具。

#新加坡租房 #新加坡condo #租房攻略 #新加坡生活 #condo租金 #开源项目 #PropTech
