const ALBUM = [
    /* 周华健 */
    {
        name: "今夜陽光燦爛 (Live)",
        artist: "周华健",
        cover: "https://i.scdn.co/image/ab67616d0000b273625702e618b971048958a11f",
        songs: ["旭日初昇 - Live","向陳揚致敬 - Live","心的方向 - Live","傷心的歌 - Live","樂不可支 - Live","勸世歌 - Live","明天我要嫁給你 - Live","北京，你好！ - Live","南泥灣 - Live","鳳陽花鼓 - Live","站在台北舞台上 - Live","親親我的寶貝 - Live","讓我歡喜讓我憂 - Live","孤枕難眠 - Live","花心 - Live","欲罷不能之 Encore - Live","我是真的付出我的愛 - Live","曲終人不散 - Live"]
    },
    {
        name: "弦猶在耳 (Live)",
        artist: "周华健",
        cover: "https://i.scdn.co/image/ab67616d0000b273846ccebc50195ba342a4069b",
        songs: ["明天我要嫁給你+昨晚你已嫁給誰 - Live","妳喜歡的會有幾個 - Live","是你叫我 - Live","為愛情受傷 - Live","You Are So Beautiful - Live","當天的心 - Live","曾經滄海也是愛 - Live","海角天涯 - Live","然後然後 - Live","風繼續吹 - Live","天才白痴夢 - Live","新天長地久之男大當戀女大當愛 - Live","濃情化不開 - Live","雪中火 - Live","多一分鐘少一分鐘 - Live","沿途有你 - Live","誰叫我 - Live"]
    },
    {
        name: "風雨無阻",
        artist: "周华健",
        cover: "https://i.scdn.co/image/ab67616d0000b2730a02f529649ccb42d94e8dcf",
        songs: ["其實不想走","風雨無阻","難兄難弟","淚該停,夢該醒","忙與盲","的確比他好","刀劍如夢","海闊天空","誰的淚","只送你十一朵玫瑰","現在時間凌晨五點三十五分 - Talking"]
    },
    /* 刘德华 */
    {
        name: "真永遠",
        artist: "刘德华",
        cover: "https://i.scdn.co/image/ab67616d0000b2734299f76b81441e59a8cb7c79",
        songs: ["真永遠","愛火燒不盡","絕不放棄","忘了隱藏","今天","等你愛你到最後","你說他是你想嫁的人","夢中見","真的愛著你","心聲共鳴","永遠是這天"]
    },
    {
        name: "忘情水",
        artist: "刘德华",
        cover: "https://i.scdn.co/image/ab67616d0000b2731253ff7ac2748e785737a796",
        songs: ["忘情水","纏綿","不該愛上你","錯怪","心酸","你是我的溫柔","癡","最孤單的人是我","峰迴路轉","想要飛"]
    },
    {
        name: "天意",
        artist: "刘德华",
        cover: "https://i.scdn.co/image/ab67616d0000b2739c6ce5dc20b20b629110d68a",
        songs: ["天意","友誼歷久一樣濃","沒有人可以像你","等你忘了我是誰","錯的都是我","浪花","念舊","我愛的是你","該說的我已說","害怕愛一回"]
    },
    /* Beyond */
    {
        name: "海闊天空",
        artist: "Beyond",
        cover: "https://i.scdn.co/image/ab67616d0000b273a11066c8f15842ae9af7e700",
        songs: ["海闊天空","爸爸媽媽","愛不容易說","和平與愛","身不由己","全是愛","情人","無無謂","くちびるを奪いたい","遙かなる夢に〜Far away〜"]
    },
    {
        name: "繼續革命",
        artist: "Beyond",
        cover: "https://i.scdn.co/image/ab67616d0000b273779a678e5b61f269afb7cd0f",
        songs: ["長城","農民","不可一世","Bye Bye","遙望","溫暖的家鄉","可否衝破","快樂王國","繼續沉醉","早班火車","厭倦寂寞","無語問蒼天"]
    },
    /* 張學友 */
    {
        name: "真情流露",
        artist: "張學友",
        cover: "https://i.scdn.co/image/ab67616d0000b27398e7cf40bb136d8da566d6d6",
        songs: ["偷閒加油站 I","愛得比你深","分手總要在雨天","Honey B","暗戀你","明日世界終結時","真情流露","歲月流情","紅葉舞秋山 - 電視劇「出位江湖」主題曲","相思風雨中 - 電視劇「出位江湖」插曲","不要再問","偷閒加油站 II"]
    },
    
    /* 郭富城 */
    {
        name: "天若有情 II - 天涯凝望",
        artist: "郭富城",
        cover: "https://i.scdn.co/image/ab67616d0000b2733a5d338a6205f642154939bd",
        songs: ["天涯凝望","你是我的1/2","就算是情人","愛你我願一生放肆","再生也只等待你","天涯","如果今生不能和你一起","只因有你我才認真","再生也只等待你 - 國語"]
    },
    {
        name: "到底有誰能夠告訴我",
        artist: "郭富城",
        cover: "https://i.scdn.co/image/ab67616d0000b2730177bcf031fc661acc7ee268",
        songs: ["我不認輸","到底有誰能夠告訴我","勇敢接受我的愛","Tell Me Why","午夜的吻別","Heart Breaker","我要給你全部的愛","喜歡就說愛","很難過還是要告訴你","Good Times & Bad Times"]
    },
    /* 鄭智化 */
    {
        name: "遊戲人間",
        artist: "鄭智化",
        cover: "https://i.scdn.co/image/ab67616d0000b273e9c5f44cc998243eb064e2d5",
        songs: ["遊戲人間","阿飛和他的那個女人","面子問題","我願意","上海灘","小草","我是風箏","新綠島小夜曲","原來的樣子","斗室",]
    },
    {
        name: "星星點燈",
        artist: "鄭智化",
        cover: "https://i.scdn.co/image/ab67616d0000b273a3d7d4c6089dcbd76525ec49",
        songs: ["星星點燈","麻花辮子","補習街","蝸牛的家","冬季","朋友 天堂好嗎","雨","南台灣","煙花江畔","不能告訴你"]
    },
    
    
];
