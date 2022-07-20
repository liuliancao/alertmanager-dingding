# 用途
接收alertmanger, 通过dingding发送告警消息，版本比较简陋，请多包涵！

# 功能
- 通过机器人单发
- webhook群发

# 配置
需要有dingding管理员开发者权限(和公司管理员申请)

参数和含义

需要新建一个dingding应用
appKey: dingding h5应用的key
appSecret: dingding h5应用的secret

需要新建一个dingding机器人
robotAppKey: 机器人的key
robotAppSecret: 机器人的secret

alertmanagerURL: 用于silence的前缀，alertmanager silence
grafanaURL: 用于根据grafanaPrefix替换成对应的grafanaURL localhost:3000会被替换成这个

prometheusURL: 用于根据prometheusPrefix替换成对应的prometheusURL localhost:9090 会被替换成这个

# 部署
参考alertmanager-dingding.service和init.pp

# 测试
curl -XPOST http://localhost:5354/ding -H 'Content-Type: application/json' -d "{\"status\": \"firing\", \"labels\": {\"__alert_rule_uid__\": \"abcd\", \"alert_ding\": \"消息测试群\", \"alert_group\": \"消息测试群\", \"alert_head\": \"test_head\", \"alertname\": \"load偏高\", \"severity\": \"critical\"}, \"annotations\": {\"__value_string__\": \"[ var='B'  value=91.61050415039062 ], [ var='C' value=1 ]\", \"summary\": \"load大于3\"}, \"startsAt\": \"2022-07-19T14:26:03.240948881+08:00\", \"endsAt\": \"0001-01-01T00:00:00Z\", \"generatorURL\": \"http://localhost:3000/alerting/grafana/abcd/view\", \"fingerprint\": \"d2d80d3739cfa23e\"}"
