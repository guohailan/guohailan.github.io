# Trojan搭建


使用trojan原版进行搭建。
<!--more-->

## 什么是Trojan

Trojan 是一个比较新的翻墙软件，它模仿了互联网上最常见的HTTPS协议，以诱骗 GFW 认为它就是 HTTPS，从而不被识别。所谓魔高一尺道高一丈，墙在不断往上砌，那工具也得跟着变了。Trojan 工作在 443 端口，并且处理来自外界的 HTTPS 请求，如果是合法的 Trojan 请求，那么为该请求提供服务，否则将该流量转交给 WEB 服务器 Nginx，由 Nginx 为其提供服务。基于这个工作过程可以知道，Trojan 的一切表现均与 Nginx 一致，不会引入额外特征，从而达到无法识别的效果。当然，为了防止恶意探测，我们需要将 80 端口的流量全部重定向到 443 端口，并且服务器只暴露 80 和 443 端口，这样可以使得服务器与常见的 WEB 服务器表现一致。

## 域名准备

域名申请可以去腾讯云或者阿里云等国内大厂申请（缺点就是需要花钱），这里我是去的免费域名商freenom申请的[http://www.freenom.com/zh/index.html](http://www.freenom.com/zh/index.html)，不过访问这个地址很慢，所以可能需要提前出去。

### 域名申请

首先注册账号，基本信息里实测国家选择<font color=#DC143C>美国</font>以外的地区可能无法注册成功，所以这里我选择的洛杉矶

![](/images/Trojan搭建/image-20210118221317622.png " ")

输入希望申请的域名，点击检查可用性

![](/images/Trojan搭建/image-20210118220651867.png " ")

选择心仪的域名后缀，点击现在获取

![](/images/Trojan搭建/image-20210118220757391.png " ")

域名时长我们一般选择最长时间1年，然后将VPS的IP填入解析地址（也可以现在不填，申请完成后在My Domains里面进行填写）

![](/images/Trojan搭建/image-20210118222157926.png " ")

### 域名测试

默认的DNS生效时间比较长，大概半小时左右。本地能ping通域名，返回的地址为希望的IP，表示域名申请成功

![](/images/Trojan搭建/image-20210118222954624.png " ")

## 证书申请

证书申请也是本着不花钱的原则，选择[https://freessl.cn/](https://freessl.cn/)

因为只有亚洲诚信可以支持双域名，而且有效期可以1年，所以选择亚洲诚信，点击创建免费的SSL证书

![](/images/Trojan搭建/image-20210118223321305.png " ")

填入个人邮箱，然后点击创建

![](/images/Trojan搭建/image-20210118223513080.png " ")

登录FreeSSL的账号，安装亚洲诚信的KeyManager

![](/images/Trojan搭建/image-20210118223709924.png " ")

点击继续后，会自动带起KeyManager，生成秘钥

![](/images/Trojan搭建/image-20210118223957243.png " ")

回到浏览器，在浏览器上会提示DNS验证

![](/images/Trojan搭建/image-20210118224709956.png " ")

这时我们回到freenom点击My Domains，点击Manage Domain，选择Manage Freenom DNS

![](/images/Trojan搭建/image-20210118224205751.png " ")

将证书生成的信息填入DNS的解析里面，Type选择TXT，然后点击保存

![](/images/Trojan搭建/image-20210118224559935.png " ")

回到freessl页面，点击配置完成（可能有30分钟左右延迟），检测一下，当检测通过，点击验证即可签发证书，证书签发以后，可以使用https访问一下自己的域名，可以看到证书是有效的

![](/images/Trojan搭建/image-20210118230001432.png " ")

## Torjan搭建

**此处我使用的是Centos7的系统**

首先安装依赖包

```shell
yum update -y && yum install sudo newt curl -y && sudo -i
```

### 安装BBR加速

```shell
wget -N --no-check-certificate "https://raw.githubusercontent.com/chiakge/Linux-NetSpeed/master/tcp.sh" && chmod +x tcp.sh && ./tcp.sh
```

选择需要的BBR加速内核，我的服务器默认已经安装了BBR内核，因此我直接选择4开启

![](/images/Trojan搭建/image-20210118225435649.png " ")

### 安装Trojan

下载一键安装脚本

```shell
curl -O https://raw.githubusercontent.com/atrandys/trojan/master/trojan_mult.sh && chmod +x trojan_mult.sh && ./trojan_mult.sh
```

根据提示信息填入域名和密码即可搭建完成，搭建完成后访问域名会出现一个网站

![](/images/Trojan搭建/image-20210118225825028.png " ")

## windows配置

脚本执行完成后会在`/usr/src/trojan-cli/trojan-cli.zip`目录下生成带有配置文件的windows软件，下载到本地解压后双击`trojan.exe`直接运行即可，详细配置见`config.json`

![](/images/Trojan搭建/image-20210118230622791.png " ")

### 安装v2rayN

到[https://github.com/2dust/v2rayN/releases](https://github.com/2dust/v2rayN/releases)下载v2rayN客户端，此处下载的是稳定版

![](/images/Trojan搭建/image-20210118231425080.png " ")

解压后运行软件，点击服务器，添加Socks服务器，填入地址如图

![](/images/Trojan搭建/image-20210118231524385.png " ")

### 验证

访问google，能正常访问，在开启的Trojan和v2rayN都能看到访问的日志，搭建成功

![](/images/Trojan搭建/image-20210118231650953.png " ")

## 安卓配置

下载Trojan安卓客户端（一般选择*-universal-release.apk）[https://github.com/trojan-gfw/igniter/releases](https://github.com/trojan-gfw/igniter/releases)，安装到手机即可

![](/images/Trojan搭建/image-20210118231237972.png " ")  

