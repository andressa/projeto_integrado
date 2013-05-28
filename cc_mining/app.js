const PORT = 4000;

var express = require('express');

var http = require('http');
var io = require('socket.io');

var redis = require('redis');
var client = redis.createClient();


if (!module.parent) {
    var server = http.createServer();
    const socket  = io.listen(server);
    server.listen(PORT);

    socket.on('connection', function(client) {
        const subscribe = redis.createClient();
        const publish = redis.createClient();
        subscribe.subscribe('cc');

        subscribe.on("message", function(channel, message) {
            client.send(message);
        });

        client.on('message', function(msg) {
            publish.publish('twist', msg);
        });

        client.on('disconnect', function() {
            subscribe.quit();
        });
    });
}
