# pptx2md

## 預先安裝

```
pip install python-pptx
# （選用）中文關鍵字擷取：
pip install jieba
```

## 使用方式

```
# 基本轉換（輸出為同名 .txt）
python pptx_to_md.py input.pptx

# 指定輸出檔名、tags 數量上限、包含備註、表格輸出為 Markdown 表格
python pptx_to_md.py input.pptx -o output.txt --max-tags 20 --include-notes --table-format table
```

## 輸出
```
# Tags
- AI
- OSS
- Postgres
...

---
# 內容
### 第 1 頁：封面標題
- 副標
- 要點一
- 要點二

### 第 2 頁：議程
- 章節一
- 章節二
...
```
