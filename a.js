function getTimerString(time,type) {
        d = Math.floor(time / 86400),
        h = Math.floor((time % 86400) / 3600),
        m = Math.floor(((time % 86400) % 3600) / 60),
        s = Math.floor(((time % 86400) % 3600) % 60);
    if (time>0 && type == 'shipping'){
        return "剩余发货：" + d + "天" + h + "小时" + m + "分";
    }else if(time>0 && type == 'tracking'){
        return "单号有效：" + d + "天" + h + "小时" + m + "分";
    }else if(time <= 0 && type == 'shipping'){
return "剩余发货：已到期";
    }else if(time <= 0 && type == 'tracking'){
        return "单号有效：已到期";
    }else if(time > 0 && type == 'issue'){
        return d + "天" + h + "小时" +  m +"分" + s + "秒";
    }
}