# ix3-TMT
ix3-TMT(Team-Management-Tool) is a tool for managing digital consultancy team-delivered professional reports.


## 報告管理 ##
團隊個人撰寫的專業報告，除了計算交付數量外，亦在團隊內交流使用。

### converters ###
#### PPT to PDF to PNG
引用： hadwinzhy/convert-ppt-to-jpg
<pre><code>sudo apt-get update && sudo apt-get install -y libreoffice openjdk-8-jdk imagemagick</code></pre>

<pre><code>#!/bin/bash

path=${1}

mkdir -p converted_jpg
##################### ppt & pptx #####################
if [[ "$path" == *"ppt"* ]]; then
  soffice --headless --convert-to pdf $path --outdir converted_jpg/
  cd converted_jpg
  convert -verbose -density 150 *.pdf -quality 100 $path".jpg"
  rm -rf *.pdf
  cd -
fi

####################### keynote ######################
if [[ "$path" == *"key"* ]]; then
   echo 'wait for keynote'
fi

echo 'please check folder converted_jpg'
</code></pre>

- 需ImageMagick修改參數
<pre><code>vim /etc/ImageMagick-6/policy.xml</code></pre>
<pre><code>policy domain="coder" rights="read|write" pattern="PDF"</code></pre>


#### 圖像呈現 ####
 - 分個人製作的內容
 - 圖像說明: 連結原檔案
 - 交付分享統計
