# goftp 125 Data connection already open问题


记录一次使用goftp包文件上传异常的问题
<!--more-->
## 问题现象

平常工作中，经常会涉及到ftp文件上传，所以使用第三方库github.com/dutchcoders/goftp，撸了个ftp上传脚本。之前使用都是正常上传，今天使用突然发现无法无法使用了，抛出的异常为`125 Data connection already open; transfer starting`，ftp服务器上文件名已经存在但是大小为0kb，因为编译成了exe格式，所以不涉及代码改动，顿时觉得比较奇怪，将代码又重新撸了一遍，未发现明显异常，报错依旧。

## 定位过程

在网上也没查到啥有用信息，只有一个ftp异常码的解释`125 Data connection already open; transfer starting.  资料连接已经打开，开始传送资料. `。后查阅ftp相关资料，ftp在文件上传的时候，是通过发送STOR命令来实现的，然后期待ftp返回150，是一个成功的响应码，后续会上传成功。但是现在只返回了一个125。查看goftp源码ftp.go，当ftp连接上以后，会返回一个状态，如果不是以`StatusFileOK`开头，则`return`  
![](/images/goftp-125-Data-connection-already-open问题/goftp_ftp.png " ")  

继续查看status.go中定义的`StatusFileOK`，定义的值为150，所以返回125会抛出异常。
![](/images/goftp-125-Data-connection-already-open问题/goftp_status.png " ")

## 原因

经过一下午的排查，原因找到了，应该是国庆期间公司对ftp的服务器进行了升级。IIS7对响应码处理做了调整。http://support.microsoft.com/kb/2505047 ，<font color=red>IIS7前，对APPE，STOU ，STOR命令，passive模式响应125，active模式响应150。IIS7.5后不考虑连接模式了，只考虑当前的连接状态，未连接响应150，已连接响应125</font>。

## 解决办法
使用了一个比较粗暴的办法，直接将源码status.go中的`StatusFileOK="150"`改为`StatusFileOK="125"`，重新编译脚本之后上传正常。因只在本地使用，未做兼容性测试。仅此记录
