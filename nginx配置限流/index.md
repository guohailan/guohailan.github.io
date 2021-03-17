# nginx配置限流


系统设计时一般会预估负载，当系统暴露在公网中时，恶意攻击或正常突发流量等都可能导致系统被压垮，而限流就是保护措施之一。限流即控制流量，本文将记录 Nginx 的一种速率限流设置。
<!--more-->
###  ngx_http_limit_req_module

ngx_http_limit_req_module模块提供限制请求处理速率能力，使用了漏桶算法(leaky bucket)，即能够强行保证请求的实时处理速度不会超过设置的阈值。
![](/images/nginx配置限流/限流算法.png " ")
算法思想是：

- 令牌以固定速率产生，并缓存到令牌桶中；
- 令牌桶放满时，多余的令牌被丢弃；
- 请求要消耗等比例的令牌才能被处理；
- 令牌不够时，请求被缓存。

### 配置示例

```nginx
http {
    #表示设置一块10m的共享内存来保存键值得状态，键为$uri，平均处理的频率不超过每秒1次
    limit_req_zone $uri zone=one:10m rate=1r/s;
    ...
    server {
        ...
        location /limittest {
            #使用共享内存one，同时允许超过频率限制的请求数不多于5个,nodelay表示不希望超过的请求被延迟
            limit_req zone=one burst=5 nodelay;
            #如果超出限制，返回429的返回码
            limit_req_status 429;
        }
```

### 参数解析

设置共享内存区域和请求的最大突发大小。如果请求速率超过为某个区域配置的速率，则它们的处理会延迟（不配置nodelay参数情况下），从而使请求按指定速率处理。过多的请求被延迟，直到它们的数量超过最大突发大小，在这种情况下请求被终止并出现错误。默认情况下，最大突发大小等于零。

`limit_req_zone key zone=zone:size rate=rate;`

**key**
- 若客户的请求匹配了key，则进入zone。可以是文本、变量，通常为Nginx变量。如$binary_remote_addr(客户的ip)，$uri(不带参数的请求地址)，$request_uri(带参数的请求地址)，$server_name(服务器名称)。支持组合使用，使用空格隔开。
**zone**
- 使用zone=one，指定此zone的名字为one。
**size**
- 在zone=name后面紧跟:size，指定此zone的内存大小。如zone=name:10m，代表name的共享内存大小为10m。通常情况下，1m可以保存16000个状态。
**rate**
- 使用rate=1r/s，限制平均1秒不超过1个请求。使用rate=1r/m，限制平均1分钟不超过1个请求。如果需要每秒小于一个请求的速率，则按每分钟请求（r/m）指定。

### 验证

编辑nginx配置文件`nginx.conf`,加入限流配置，
先执行`nginx -t`检查配置是否ok，如果返回success表示文件检查ok

![](/images/nginx配置限流/文件检查.png " ")

然后执行`nginx -s reload`重启nginx，使配置生效
浏览器访问配置了限流的url进行验证，可以看到有429返回，表示限流配置生效
![](/images/nginx配置限流/限流验证.png " ")

### 跳转自定义页面

nginx触发限流后返回的页面非常不友好，因此我们可以开启自定义error页面，使返回页面更加友好

下面这段代码可以配置在server级别，也可以配置在location级别，为了不影响别的文根，此处我们在location下配置

```nginx
location /limittest {
    ...
    # 关键参数：这个变量开启后，我们才能自定义错误页面，当后端返回429，nginx拦截错误定义错误页面
    fastcgi_intercept_errors on;
    error_page  429 /429.html;
    #error_page 429 = http://www.test.com/429.html; 也可以重定向到另一个url
    ...
}
```

`注意`:如果nginx返回的是本地的html，则页面状态码和定义的相同。若是跳转到某个url，页面状态码为302。

### nginx常见内置变量
- $args #这个变量等于请求行中的参数。
- $content_length #请求头中的Content-length字段。
- $content_type #请求头中的Content-Type字段。
- $document_root #当前请求在root指令中指定的值。
- $host #请求主机头字段，否则为服务器名称。
- $http_user_agent #客户端agent信息
- $http_cookie #客户端cookie信息
- $limit_rate #这个变量可以限制连接速率。
- $request_body_file #客户端请求主体信息的临时文件名。
- $request_method #客户端请求的动作，通常为GET或POST。
- $remote_addr #客户端的IP地址。
- $remote_port #客户端的端口。
- $remote_user #已经经过Auth Basic Module验证的用户名。
- $request_filename #当前请求的文件路径，由root或alias指令与URI请求生成。
- $query_string #与$args相同。
- $scheme #HTTP方法（如http，https）。
- $server_protocol #请求使用的协议，通常是HTTP/1.0或HTTP/1.1。
- $server_addr #服务器地址，在完成一次系统调用后可以确定这个值。
- $server_name #服务器名称。
- $server_port #请求到达服务器的端口号。
- $request_uri #包含请求参数的原始URI，不包含主机名，如：”/foo/bar.php?arg=baz”。
- $uri #不带请求参数的当前URI，$uri不包含主机名，如”/foo/bar.html”。
- $document_uri #与$uri相同。
