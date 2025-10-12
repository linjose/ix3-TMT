# Announcement 功能
放置公告功能

部署說明（摘要）：
1) 將此檔案存為 /index.html。
2) 在網站根目錄建立 post/ 目錄，放入多個 JSON 檔（檔名採 YYYYMMDDHHmm.json）。

每個 JSON 需包含：{"title":"...","date":"2025-09-25T14:00:00+08:00","content":"..."}
* 若不提供 date，會從檔名解析排序。
3) 於 post/ 目錄放置 index.json（內容為檔名陣列），例如：
["202509251400.json", "202509221230.json"]
可用下方提供的 Node 腳本在建置時自動產生。
4) 將專案部署至 Netlify（不需打包流程亦可）、Apache2、Nginx等亦可。


### free counter
Add counter
```
<img src='https://www.counter12.com/img-ca5ZZAx047b344w9-57.gif' border='0' alt='counter'><script type='text/javascript' src='https://www.counter12.com/ad.js?id=ca5ZZAx047b344w9'></script>                               
```
