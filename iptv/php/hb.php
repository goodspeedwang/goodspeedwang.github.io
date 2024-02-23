<?php
$fmt = isset($_GET['fmt'])?$_GET['fmt']:'hls';
$r='http://app.cjyun.org/';

if($fmt=='ts'){
    $p = $_GET['p'];
    $ts = $_GET['ts'];
    $ak = $_GET['ak'];
    header("Content-type: video/mp2t");
    $d = ts(trim($p).trim($ts).'?auth_key='.trim($ak),$r);
}else if($fmt=='hls'){
    $id = isset($_GET['id'])?$_GET['id']:'hbws';
    header("Content-type: application/x-mpegURL");
    $n = array(
        'hbws' => ['10008','431'], //湖北卫视
        'hbjs' => ['10008','432'], //湖北经视
        'hbzh' => ['10008','433'], //湖北综合
        'hbgg' => ['10008','434'], //湖北公共新闻
        'hbys' => ['10008','435'], //湖北影视
        'hbsh' => ['10008','436'], //湖北生活
        'hbjy' => ['10008','437'], //湖北教育
        'hbls' => ['10008','438'], //湖北垄上
        'mjgw' => ['10008','439'], //美嘉购物
    );
    $m = array(
        'wxzh' => ['http://wuxue-live21.cjyun.org/10107/','s10107-wxtv1.m3u8','1672502399-0-0-496875cc106b717ff79100d9d50109b9'], //武穴综合
        'ltzh' => ['http://luotian-live21.cjyun.org/10013/','s10013-LTZH.m3u8','1672502399-0-0-299e343438656b23a3aa539c70fdca53'],//罗田综合
        'ltly' => ['http://luotian-live21.cjyun.org/10013/','s10013-LTLY.m3u8','1672502399-0-0-9abbdb17dd5c3e9a9ed01da316bff455'],//罗田旅游
        'qczh' => ['http://qichun-live21.cjyun.org/10126/','s10126-TC1T.m3u8','1672502399-0-0-b3a552ec258aa7e67f50ab3557190bea'], //蕲春综合
    );
    if(!!$n[$id]) {
        $d = file_get_contents('http://app.cjyun.org/video/player/stream?site_id='.$n[$id][0].'&stream_id='.$n[$id][1]);
        $json = json_decode($d);
        $playurl = $json->stream;
        $m3u8 = m3u8($playurl,$r);
        $phpself=substr($_SERVER['PHP_SELF'],strripos($_SERVER['PHP_SELF'],"/")+1);
        echo str_replace('?auth_key=','&ak=',str_replace('live21.hbtv.com.cn',$phpself.'?fmt=ts&p=http://live21-cjy.hbtv.com.cn/hbtv/&ts=live21.hbtv.com.cn',$m3u8));
    }
    if(!!$m[$id]) {
        $playurl = $m[$id][0].$m[$id][1].'?auth_key='.$m[$id][2];
        $m3u8 = m3u8($playurl,$r);
        $phpself=substr($_SERVER['PHP_SELF'],strripos($_SERVER['PHP_SELF'],"/")+1);
        echo str_replace('?auth_key=','&ak=',str_replace('live21.hbtv.com.cn',$phpself.'?fmt=ts&p='.$m[$id][0].'&ts=live21.hbtv.com.cn',$m3u8));
    }
}


function m3u8($url,$ref){
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);
    curl_setopt ($ch, CURLOPT_REFERER, $ref);
    $result = curl_exec($ch);
    curl_close($ch);
    return $result;
}

function ts($url,$ref){
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
    curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, FALSE);
    curl_setopt ($ch, CURLOPT_REFERER, $ref);
    $result = curl_exec($ch);
    curl_close($ch);
}
?>