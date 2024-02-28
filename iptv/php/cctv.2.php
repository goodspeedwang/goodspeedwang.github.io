<?php
/*
4K0219,http://iptv.home/cctv.2.php?id=4K0219.stream
4K36M,http://iptv.home/cctv.2.php?id=4K36M
CCTV16-4K,http://iptv.home/cctv.2.php?id=CCTV16-4K.stream
*/
$id=isset($_GET['id'])?$_GET['id']:'4K0219.stream';

$hostname = 'liveali-tpgq.cctv.cn';

// 获取域名的 IPv4 地址
$ip = gethostbyname($hostname);

// 构建 URL
$url = "http://{$ip}/liveali-tp4k.cctv.cn/live/" . $id ."/playlist.m3u8";

header('location:'   . $url);
?>