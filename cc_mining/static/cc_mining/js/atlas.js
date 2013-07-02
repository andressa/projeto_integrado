(function(){

  Renderer = function(canvas){
    var canvas = $(canvas).get(0)
    var ctx = canvas.getContext("2d");
    var gfx = arbor.Graphics(canvas)
    var particleSystem = null

  	// helpers for figuring out where to draw arrows (thanks springy.js)
  	var intersect_line_line = function(p1, p2, p3, p4)
  	{
  		var denom = ((p4.y - p3.y)*(p2.x - p1.x) - (p4.x - p3.x)*(p2.y - p1.y));
  		if (denom === 0) return false // lines are parallel
  		var ua = ((p4.x - p3.x)*(p1.y - p3.y) - (p4.y - p3.y)*(p1.x - p3.x)) / denom;
  		var ub = ((p2.x - p1.x)*(p1.y - p3.y) - (p2.y - p1.y)*(p1.x - p3.x)) / denom;

  		if (ua < 0 || ua > 1 || ub < 0 || ub > 1)  return false
  		return arbor.Point(p1.x + ua * (p2.x - p1.x), p1.y + ua * (p2.y - p1.y));
  	}

  	var intersect_line_box = function(p1, p2, boxTuple)
  	{
  	  var p3 = {x:boxTuple[0], y:boxTuple[1]},
      	  w = boxTuple[2],
      	  h = boxTuple[3]
  	  
  		var tl = {x: p3.x, y: p3.y};
  		var tr = {x: p3.x + w, y: p3.y};
  		var bl = {x: p3.x, y: p3.y + h};
  		var br = {x: p3.x + w, y: p3.y + h};

      return intersect_line_line(p1, p2, tl, tr) ||
             intersect_line_line(p1, p2, tr, br) ||
             intersect_line_line(p1, p2, br, bl) ||
             intersect_line_line(p1, p2, bl, tl) ||
             false
  	}
  	
  	
    var that = {
      //
      // the particle system will call the init function once, right before the
      // first frame is to be drawn. it's a good place to set up the canvas and
      // to pass the canvas size to the particle system
      //
      init:function(system){
        // save a reference to the particle system for use in the .redraw() loop
        particleSystem = system

        // inform the system of the screen dimensions so it can map coords for us.
        // if the canvas is ever resized, screenSize should be called again with
        // the new dimensions
        particleSystem.screenSize(canvas.width, canvas.height) 
        particleSystem.screenPadding(40) // leave an extra 20px of whitespace per side

        that.initMouseHandling()
      },
      
      // 
      // redraw will be called repeatedly during the run whenever the node positions
      // change. the new positions for the nodes can be accessed by looking at the
      // .p attribute of a given node. however the p.x & p.y values are in the coordinates
      // of the particle system rather than the screen. you can either map them to
      // the screen yourself, or use the convenience iterators .eachNode (and .eachEdge)
      // which allow you to step through the actual node objects but also pass an
      // x,y point in the screen's coordinate system
      // 

      redraw:function(){
        if (!particleSystem) return
                
        ctx.clearRect(0,0, canvas.width, canvas.height)

        var nodeBoxes = {}
        particleSystem.eachNode(function(node, pt){
          // node: {mass:#, p:{x,y}, name:"", data:{}}
          // pt:   {x:#, y:#}  node position in screen coords
          

          // determine the box size and round off the coords if we'll be 
          // drawing a text label (awful alignment jitter otherwise...)
          var label = node.data.label||""
          var w = ctx.measureText(""+label).width + 10
          if (!(""+label).match(/^[ \t]*$/)){
            pt.x = Math.floor(pt.x)
            pt.y = Math.floor(pt.y)
          }else{
            label = null
          }
          
          // draw a rectangle centered at pt
          if (node.data.color) ctx.fillStyle = node.data.color
          // else ctx.fillStyle = "#d0d0d0"
          else ctx.fillStyle = "rgba(250,0,0,.6)"
          if (node.data.color=='none') ctx.fillStyle = "white"
          
          
          // ctx.fillRect(pt.x-w/2, pt.y-10, w,20)
          if (node.data.shape=='dot'){
             gfx.oval(pt.x-w/2, pt.y-w/2, w,w, {fill:ctx.fillStyle})
             nodeBoxes[node.name] = [pt.x-w/2, pt.y-w/2, w,w]
          }else{
            gfx.rect(pt.x-w/2, pt.y-10, w,20, 4, {fill:ctx.fillStyle})
            nodeBoxes[node.name] = [pt.x-w/2, pt.y-11, w, 22]
          }

          // w = Math.max(20,w)

          // draw the text
          if (label){
            ctx.font = "12px Helvetica"
            ctx.textAlign = "center"
            ctx.fillStyle = "white"
            if (node.data.color=='none') ctx.fillStyle = '#333333'
            ctx.fillText(label||"", pt.x, pt.y+4)
            ctx.fillText(label||"", pt.x, pt.y+4)
          }
        })    			


        ctx.strokeStyle = "#cccccc"
        ctx.lineWidth = 1
        ctx.beginPath()
        particleSystem.eachEdge(function(edge, pt1, pt2){
          // edge: {source:Node, target:Node, length:#, data:{}}
          // pt1:  {x:#, y:#}  source position in screen coords
          // pt2:  {x:#, y:#}  target position in screen coords

          var weight = edge.data.weight
          var color = edge.data.color

          // trace(color)
          if (!color || (""+color).match(/^[ \t]*$/)) color = null

          // find the start point
          var tail = intersect_line_box(pt1, pt2, nodeBoxes[edge.source.name])
          var head = intersect_line_box(tail, pt2, nodeBoxes[edge.target.name])

          ctx.save() 
            ctx.beginPath()

            if (!isNaN(weight)) ctx.lineWidth = weight
            if (color) ctx.strokeStyle = color
            ctx.fillStyle = null
            ctx.fillStyle = "black";
            ctx.font = 'italic 16px';
            ctx.fillText ("n=" + edge.data.n, (pt1.x + pt2.x) / 2, (pt1.y + pt2.y) / 2);

            ctx.moveTo(tail.x, tail.y)
            ctx.lineTo(head.x, head.y)
            ctx.stroke()
          ctx.restore()

        })



      },
      initMouseHandling:function(){
        // no-nonsense drag and drop (thanks springy.js)
      	selected = null;
      	nearest = null;
      	var dragged = null;
        var oldmass = 1


        var handler = {
          clicked:function(e){
        		var pos = $(canvas).offset();
        		_mouseP = arbor.Point(e.pageX-pos.left, e.pageY-pos.top)
        		selected = nearest = dragged = particleSystem.nearest(_mouseP);
            
            if (dragged.node !== null) dragged.node.fixed = true
//        		if  (selected.node !== null) dragged.node.tempMass = 10000
        		      		
            $(canvas).bind('mousemove', handler.dragged)
        		$(window).bind('mouseup', handler.dropped)
      		
        		return false
          },
          dragged:function(e){
            var old_nearest = nearest && nearest.node._id
        		var pos = $(canvas).offset();
        		var s = arbor.Point(e.pageX-pos.left, e.pageY-pos.top)

            if (!nearest) return
        		if (dragged !== null && dragged.node !== null){
              var p = particleSystem.fromScreen(s)
        			dragged.node.p = p//{x:p.x, y:p.y}
//        			dragged.tempMass = 100000
        		}

            return false
        	},

          dropped:function(e){
            if (dragged===null || dragged.node===undefined) return
            if (dragged.node !== null) dragged.node.fixed = false
            dragged.node.tempMass = 1000
            dragged = null;
            selected = null
            $(canvas).unbind('mousemove', handler.dragged)
        		$(window).unbind('mouseup', handler.dropped)
            _mouseP = null
            return false
          }

          
        }
        
        $(canvas).mousedown(handler.clicked);
      	
      },
    	
    }
    return that
  };

    function comp(a,b) {
        return parseInt(a, 10) - parseInt(b, 10);
    }

    function process_edges(edges, correlations) {

        var colors = ['blue', 'green', 'yellow', 'orange', 'red', 'black']
        var division = parseInt(correlations.length/colors.length, 10)
        for (var e in edges) {
            var targets = edges[e];
            for (var t in targets) {
                var w = targets[t].n;
                if (w < correlations[0, division])
                    targets[t].color = "rgb(40,91,184)";
                else if (w < correlations[division, 2*division])
                    targets[t].color = 'rgb(93, 157, 67)';
                else if (w < correlations[2*division, 3*division])
                    targets[t].color = 'rgb(206, 181, 19)';
                else if (w < correlations[3*division, 4*division])
                    targets[t].color = 'rgb(206, 103, 19)';
                else if (w < correlations[4*division, 5*division])
                    targets[t].color = 'rgb(193, 53, 31)';
                else
                    targets[t].color = 'black';
            }
        }
        console.log(edges);
        return edges;

    }

    var Novelas = function(data){
        /*
         arbor.ParticleSystem(repulsion, stiffness, friction, gravity, fps, dt, precision)

         The parameters and their defaults are:
         repulsion  1,000       the force repelling nodes from each other
         stiffness  600         the rigidity of the edges
         friction   0.5         the amount of damping in the system
         gravity    false       an additional force attracting nodes to the origin
         fps        55 frames per second
         dt         0.02        timestep to use for stepping the simulation
         precision  0.6         accuracy vs. speed in force calculations
                    (zero is fast but jittery, one is smooth but cpu-intensive)
         *
         */
        var correlations = [];
        for (var e in data.edges) {
            var targets = data.edges[e];
            for (var t in targets) {
                var w = targets[t].n;
                if (correlations.indexOf(w) == -1) correlations.push(w);
            }
        }
        correlations.sort(comp);
        var edges = process_edges(data.edges, correlations);
        var sys = arbor.ParticleSystem(15600, 10, 0.0, true, 300);
        sys.renderer = Renderer("#viewport");

        var nodes = data.nodes;
        $.each(nodes, function(name, info){
            info.label=name.replace(/(people's )?republic of /i,'').replace(/ and /g,' & ')
        });

        sys.merge({nodes:nodes, edges:edges});
    };

    $(document).ready(function(){

      Novelas(JSON.parse(localStorage.getItem('data')));

    });

})();
