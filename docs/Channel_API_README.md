# Tapis V3 Streams Channel API
REST API for managing Streams Channel.

### Quickstart

#### Templates
 A template has three required fields: `template_id`, `type`, `script`.

To test templates API, we recommend to use Postman app as the `script` field involves lots of escaping of special characters in a cURL command.
 A template can be created like so:

 ```
POST http://localhost:5000/v3/streams/templates
Header  Content-Type: application/json
Header  X-Tapis-Token: $TOKEN
JSON request body:
{   
	"template_id":"tapis_template",
	"type":"stream",
	"script":"var period=5s\n var every=0s\n var crit lambda \n var channel_id string\n stream\n    |from()\n        .measurement('tsdata')\n         .groupBy('var')\n     |window()\n        .period(period)\n         .every(every)\n         .align()\n     |alert()\n        .id(channel_id +  ' {{ .Name }}/{{ .Group }}/{{.TaskName}}/{{index .Tags \"var\" }}')\n         .crit(crit)\n         .message('{{.ID}} is {{ .Level}} at time: {{.Time}} as value: {{ index .Fields \"value\" }} exceeded the threshold')\n        .details('')\n         .post()\n         .endpoint('api-alert')\n     .captureResponse()\n    |httpOut('msg')"

}```

Expected Response:
```
{
    "message": "Template Created",
    "result": {
        "create_time": "2020-05-21 00:52:33.120704",
        "permissions": {
            "users": [
                "streamsTACCAdmin"
            ]
        },
        "script": "var period=5s\n var every=0s\n var crit lambda \n var channel_id string\n stream\n    |from()\n        .measurement('tsdata')\n         .groupBy('var')\n     |window()\n        .period(period)\n         .every(every)\n         .align()\n     |alert()\n        .id(channel_id +  ' {{ .Name }}/{{ .Group }}/{{.TaskName}}/{{index .Tags \"var\" }}')\n         .crit(crit)\n         .message('{{.ID}} is {{ .Level}} at time: {{.Time}} as value: {{ index .Fields \"value\" }} exceeded the threshold')\n        .details('')\n         .post()\n         .endpoint('api-alert')\n     .captureResponse()\n    |httpOut('msg')",
        "template_id": "tapis_template",
        "type": "stream"
    },
    "status": "success",
    "version": "dev"
}
 ```
Template list can be obtained by making a `GET` request to `/templates` end-point.

To obtain a template information, make a `GET` request to `/templates/<template_id>`

A template can be updated like so:
```
POST http://localhost:5000/v3/streams/templates
Header  Content-Type: application/json
Header  X-Tapis-Token: $TOKEN
JSON request body:
{   
	"template_id":"tapis_template",
	"type":"stream",
	"script":"var period=5s\n var every=1s\n var crit lambda \n var channel_id string\n stream\n    |from()\n        .measurement('tsdata')\n         .groupBy('var')\n     |window()\n        .period(period)\n         .every(every)\n         .align()\n     |alert()\n        .id(channel_id +  ' {{ .Name }}/{{ .Group }}/{{.TaskName}}/{{index .Tags \"var\" }}')\n         .crit(crit)\n         .message('{{.ID}} is {{ .Level}} at time: {{.Time}} as value: {{ index .Fields \"value\" }} exceeded the threshold')\n        .details('')\n         .post()\n         .endpoint('api-alert')\n     .captureResponse()\n    |httpOut('msg')"

}
```
Note that you are not allowed to change `template_id` and `type` field. The `script` can be updated unless there is no breaking changes for the tasks using the template

In the future, we plan to add publish flag to the template. Once a template is published, it cannot be updated.

#### Channel
A channel can be created like so:
```
POST http://localhost:5000/v3/streams/channels
Header  Content-Type: application/json
Header  X-Tapis-Token: $TOKEN
JSON request body:
{  
	"channel_id": "abacoTest12",
    "channel_name": "streams.abaco.test",
	"task_id" : "abacoTest12",
    "template_id":"tapis_template",
    "triggers_with_actions":[
		{
			"inst_ids":["1ab"],
			"condition": {"key":"1ab.temp", "operator":">", "val":91.0},
    		"action":{
        	"method": "ACTOR",
        	"actor_id":"4VQZ540z1P3Gm",
            "message": "Instrument: 1ab temp exceeded threshold ",
            "abaco_base_url":"https://api.tacc.utexas.edu",
            "nonces":""}
            }]


    }
```
Expected Response:
```
{
    "message": "Channel Created",
    "result": {
        "channel_id": "abacoTest12",
        "channel_name": "streams.abaco.test",
        "create_time": "2020-05-21 00:56:45.925735",
        "permissions": {
            "users": [
                "streamsTACCAdmin"
            ]
        },
        "status": "ACTIVE",
        "task_id": "abacoTest12",
        "template_id": "tapis_template",
        "triggers_with_actions": [
            {
                "action": {
                    "abaco_base_url": "https://api.tacc.utexas.edu",
                    "actor_id": "4VQZ540z1P3Gm",
                    "message": "Instrument: 1ab temp exceeded threshold ",
                    "method": "ACTOR",
                    "nonces": ""
                },
                "condition": {
                    "key": "1ab.temp",
                    "operator": ">",
                    "val": 91.0
                },
                "inst_ids": [
                    "1ab"
                ]
            }
        ]
    },
    "status": "success",
    "version": "dev"
}
```
To obtain Channel list make a `GET` request to `/channels` end-point.

To obtain a channel information, make a `GET` request to `/channels/<channel_id>`

To change channel status from `ACTIVE` to `INACTIVE`, make a `POST` request to `/channels/<channel_id>` like so :
```
POST http://localhost:5000/v3/streams/channels/abacoTest12
Header  Content-Type: application/json
Header  X-Tapis-Token: $TOKEN
JSON body:
{"status": "INACTIVE"}
```
#### Alerts
To get alerts list for a channel, make a `GET` request to `/channels/<channel_id>/alerts`.
