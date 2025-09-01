  <!--
  ========================= 伺服端（Apache）簡易說明 =========================
  一、最簡 PHP 端點（/upload.php）
  ---------------------------------  -->
  <?php
  // 確保在 Apache 上啟用 PHP（或使用 php-fpm）。
  // 建議在虛擬主機中設定：upload_max_filesize、post_max_size、max_file_uploads 等。
  header('Content-Type: application/json; charset=utf-8');
  if (!isset($_FILES['file'])) {
    http_response_code(400);
    echo json_encode(['ok'=>false,'error'=>'No file field']); exit;
  }
  $f = $_FILES['file'];
  if ($f['error'] !== UPLOAD_ERR_OK) {
    http_response_code(400);
    echo json_encode(['ok'=>false,'error'=>'Upload error','code'=>$f['error']]); exit;
  }
  // 目標資料夾（請確保 Apache 寫入權限）
  $targetDir = __DIR__ . '/uploads';
  if (!is_dir($targetDir)) { mkdir($targetDir, 0775, true); }
  // 安全檔名
  $base = basename($f['name']);
  $safe = preg_replace('/[^A-Za-z0-9._-]/','_', $base);
  $dest = $targetDir . '/' . $safe;
  if (!move_uploaded_file($f['tmp_name'], $dest)){
    http_response_code(500);
    echo json_encode(['ok'=>false,'error'=>'move_uploaded_file failed']); exit;
  }
  echo json_encode(['ok'=>true,'name'=>$safe,'size'=>$f['size'],'path'=>'/uploads/'.$safe]);
  ?>

  <!--
  二、Apache 設定重點
  ---------------------
  1) 若使用 .htaccess 控制：
     php_value upload_max_filesize 100M
     php_value post_max_size 110M
     php_value max_file_uploads 20

  2) 目錄權限：
     uploads 目錄需讓 Apache 使用者（如 www-data 或 apache）可寫入。

  3) 若不用 PHP，可改用：
     - CGI/WSGI：自行撰寫接收 multipart/form-data 的腳本。
     - WebDAV：啟用 mod_dav、mod_dav_fs，設定可寫入的 DAV 位置（需權限控管）。

  三、安全建議
  --------------
  - 驗證副檔名與 MIME Type；對可執行檔上傳一律拒絕。
  - 上傳後端目錄以純靜態方式服務，避免直接執行上傳檔案。
  - 對上傳檔案重新命名並置入隔離目錄；必要時做防毒掃描。
  - 如需認證，於前端夾帶 Token（自訂 Header），後端驗證。
  ============================================================================
  -->
