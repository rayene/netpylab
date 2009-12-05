from math import atan2, pi
from scapy.utils import colgen 


from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet 
from reportlab.rl_config import defaultPageSize 
from reportlab.lib.units import inch 
from reportlab.graphics.charts.textlabels import Label
from reportlab.graphics import shapes
from reportlab.lib import colors



    

class Action(object):
    def __init__(self, sprite = None, size = 3, color = colors.black, travel=True, travel_desc=False):
        self.sprite = sprite
        self.size = size
        self.color = color
        self.travel = travel
        self.travel_desc = travel_desc
        
class Report(object):
    #TODO: Clean
    PAGE_HEIGHT=defaultPageSize[1]; PAGE_WIDTH=defaultPageSize[0] 
    styles = getSampleStyleSheet() 
    
    def __init__(self, world, actors, file, xzoom = 200, yzoom = 500, px = 100, py = 100, detailed = False):
        self.world = world
        self.xzoom, self.yzoom = xzoom, yzoom
        self.detailed = detailed
        self.sequence_diagram = shapes.Drawing()
        self.legend = shapes.Drawing()
        
        self.file = file

        self.min_y = 0
        self.max_y = 0
        self.max_x = 0
        self.verticals = {}
        for i, actor in enumerate(actors):
            if type(actor) == tuple:
                for j, a in enumerate(actor):
                    self.verticals[a] = self.max_x = xzoom * i + j*20
            else:
                self.verticals[actor] = self.max_x = xzoom * i

    def draw_interface_history(self):
        print 'Reporting interfaces history'
        story = []
        for obj in self.world.nodes + self.world.interfaces :
            try:
                title = Paragraph('<b> %s (%s of %s)</b>' % (obj.label, obj.__class__.__name__, obj.node.label), styles['Heading2'])
            except:
                title = Paragraph('<b> %s (%s)</b>' % (obj.label, obj.__class__.__name__), styles['Heading2'])
            
            l = [['Time', 'Event', 'Description']]
            for (time, event, description)  in obj.history:
                l.append([time, event, description])
            table = Table(l, [40, 200, 300])
            table.setStyle(TableStyle([
                        ('VALIGN',(0,0),(-1,-1),'TOP'), 
                        ('INNERGRID', (0,0), (-1,-1), 0.1, colors.black), 
                        ('BOX', (0,0), (-1,-1), 0.1, colors.black), 
                        ]))
            story.extend([Spacer(1,0.2*inch), title, table])

        return story
            
            
    def draw_travels(self):
        for p in self.world.packets:
            if self.detailed:
                txt = p.command()
            else:
                txt = "(%d) %s" % (p.number, p.description)
            last_action = (0,0)
            for ts in p.trip:
                action = self.packet_actions[ts.action]
                if ts.actor not in self.verticals:
                    self.verticals[ts.actor] = self.verticals[ts.actor.node]
                x2,y2 = self.verticals[ts.actor], -ts.time*self.yzoom
                if action.sprite:
                    self.sequence_diagram.add(shapes.Circle(x2, y2, 
                    action.size,  fillColor=action.color, strokeWidth=1 ))

                if action.travel:
                    if action.travel_desc:
                        # self.sequence_diagram.add(shapes.String((last_action[0] + x)/2,(last_action[1]+y)/2, label, fill=colors.black, textAnchor = 'middle'))
                        x1, y1 = last_action[0], last_action[1]
                        l = Label()
                        l.setText(txt) 
                        l.angle = atan2((y2-y1)/2, (x2-x1))*360.0/pi
                        l.dy = 10
                        l.setOrigin((x1 + x2)/2,(y1+y2)/2)
                        self.sequence_diagram.add(l)
                        
                        #anchor = Paragraph('<a name="diagram%d"/>' %p.number, styles['Normal'])
                    self.sequence_diagram.add(shapes.Line(last_action[0],last_action[1],x2,y2, strokeColor=colors.black, strokeWidth=1))
                    self.max_y = min(y2, self.max_y, last_action[1])
                last_action = (x2,y2)

    def draw_verticals(self):
        for actor, x in self.verticals.iteritems():
            linecolor = colors.black
            if hasattr(actor, 'interfaces'):
                linecolor = colors.blue
            self.sequence_diagram.add(shapes.Line(x,self.min_y,x,self.max_y, strokeColor=linecolor, strokeWidth=1))
            self.sequence_diagram.add(shapes.String(x,self.min_y -10, actor.label, textAnchor = 'middle', fillColor=linecolor))

    def draw_timeline(self):
        time_label = 0.0
        while time_label*self.yzoom < -self.max_y:
            y = -time_label*self.yzoom
            self.sequence_diagram.add(shapes.Line(-2, y, 0 , y))
            self.sequence_diagram.add(shapes.String(-16, y, str(time_label)))
            time_label += 0.1

    def draw_legend(self):
        
        y = 0
        for name, action in self.packet_actions.iteritems():
            if action.sprite:
                self.legend.add(shapes.Circle(0, y, 
                    action.size,  fillColor=action.color, strokeWidth=1 ))
                self.legend.add(shapes.String(10,y, name))
                y+=10

    def draw_packet_history(self):
        print 'Reporting Packets History'
        story = []
        style = styles["Normal"] 
        style.fontColor = colors.black
        style2 = style
        style2.fontSize = 8
        style2.leading = 8
        # print dir(style)
        for p in self.world.packets:
            # l1 = Paragraph('<a href="#diagram%d"><b>(%d)  %s</b></a>' % (p.number, p.number, p.description), styles['Heading1'])
            l1 = Paragraph('<b>(%d)  %s</b>' % (p.number, p.description), styles['Heading1'])
            style.textColor = colors.blue
            style.textColor = colors.red
            l3 = Paragraph(p.command(), styles['Heading1'])
            style.textColor = colors.indigo
            story.append(l1)
            
            l = [['Time', 'Action', 'Summary']]
            last_command = ''
            for ts in p.trip:
                act = self.packet_actions[ts.action]
                s = act.size
                if act.sprite:
                    dr = shapes.Drawing(s,s)
                    dr.add(shapes.Circle(s/2, s/2, s,  fillColor=act.color, strokeWidth=1 ))
                else:
                    dr = Paragraph('', style)
                time = Paragraph('<a name="summary%d"/><link href="#summary%d">%3.3f</link>' % (p.number, p.number, ts.time), style)
                command = ts.data.command()
                if command <> last_command:
                    last_command = command
                    command = command.replace('/','/<br/>')
                    command = Paragraph(command , style2)
                else:
                    command = '//'
                desc = '__' + ts.action + ' by ' + str(ts.actor)
                if ts.info <> '':
                    desc += '<br/>(' + ts.info +')'
                desc = Paragraph(desc, style)
                l.append([time , [dr, desc] , command])
            t = Table(l, [40, 110, 400])
            t.setStyle(TableStyle([
                        # ('ALIGN',(0,0),(-1,-1),'LEFT'), 
                                                ('VALIGN',(0,0),(-1,-1),'TOP'), 
                        #                         ('VALIGN',(1,1),(1,-1), 'MIDDLE'), 
                        #                         ('ALIGN',(1,1),(1,-1),'CENTER'), 
                        #                         ('BACKGROUND', (0, 0), (0, -1), colors.gainsboro),
                        ('INNERGRID', (0,0), (-1,-1), 0.1, colors.black), 
                        ('BOX', (0,0), (-1,-1), 0.1, colors.black), 
                        ]))

            story.append(t)
            story.append(Spacer(1,0.2*inch)) 
            style.textColor = colors.black
        return story
    
    
    def draw_hex(self):
        print 'Reporting Hex'
        story = []
        for p in self.world.packets:
            pl,t = p.build_ps()
            XSTART = 0
            XDSTART = 210
            y = 0.0
            XMUL= 100.0
            YMUL = 10.0
            larg = 16
            YDUMP = PAGE_HEIGHT*0.80/YMUL - 10
            YDUMP = 0
            canvas = shapes.Drawing(500, 100)
            # canvas.add(shapes.Rect(0,0, 500, PAGE_HEIGHT, fillColor=colors.yellow))
            backcolor=colgen(0.6, 0.8, 1.0)
            forecolor=colgen(0.2, 0.5, 0.8)
            def hexstr(x):
                s = []
                for c in x:
                    s.append("%02x" % ord(c))
                return " ".join(s)

            my_y = 0
            shift = 0
            last_x = 0
            while t:
                bkcol = backcolor.next()
                proto,fields = t.pop()
                l = Label()
                l.setText(proto.name)
                l.boxAnchor = 'w'
                l.boxStrokeColor = colors.gray
                bc = colors.Color(bkcol[0], bkcol[1], bkcol[2] )
                l.boxFillColor = bc
                l.setOrigin(XSTART, (YDUMP-y)*YMUL)
                canvas.add(l)
                my_y = y
                for fname, fval, fdump in fields:
                    y += 1.5
                    col = forecolor.next()
                    l = Label()
                    l.boxAnchor = 'w'
                    l.setText(fname.name)
                    l.setOrigin(XSTART + (0.1 * XMUL), (YDUMP-y)*YMUL)
                    canvas.add(l)
                    
                    if fval is not None:
                        if len(fval) > 24:
                            fval = fval[:21]+"..."
                    else:
                        fval=""
                    
                    l = Label()
                    l.setText(fval)
                    xlabel, ylabel = XSTART+(1.5*XMUL), (YDUMP-y)*YMUL
                    l.setOrigin(xlabel, ylabel)
                    l.boxStrokeWidth = 2
                    l.boxAnchor = 'e'
                    canvas.add(l)
                    
                    first = True
                    while fdump:
                        dmp, fdump = fdump[:larg-shift],fdump[larg-shift:]
                        l = Label()
                        l.boxAnchor = 'w'
                        l.fontName = 'Courier'
                        l.boxFillColor = colors.Color(bkcol[0], bkcol[1], bkcol[2])
                        l.boxStrokeColor = colors.Color(col[0], col[1], col[2])
                        l.boxStrokeWidth = 2
                        xdump, ydump = XDSTART+ last_x * 0.06*XMUL, (YDUMP-my_y)*YMUL
                        l.setOrigin(xdump, ydump)
                        h = hexstr(dmp)
                        l.setText(h)
                        canvas.add(l)
                        if first:
                            link = shapes.Line(xdump, ydump, xlabel, ylabel, strokeColor=colors.Color(col[0], col[1], col[2]), strokeWidth=1)
                            canvas.add(link)
                            first = False
                        shift += len(dmp)
                        last_x += len(h) +1
                        if shift >= larg:
                            shift = 0
                            last_x = 0
                            my_y += 2
                y += 2
            scale = 0.7
            canvas.shift(0, y * YMUL*scale)
            canvas.height = min(y * YMUL *scale , PAGE_HEIGHT*0.80)
            canvas.scale(scale, scale)
            # para = Paragraph('<a name="hex%d"/>'%p.number + \
            # '<a href="#summary%d">(%d) %s</a>' % (p.number, p.number, p.description), styles['Normal'])
            # story.append([[para, Spacer(1,10), canvas]])
            para = Paragraph('<a href="#summary%d">(%d) %s</a>' % (p.number, p.number, p.description), styles['Normal'])
            story.append([[para, Spacer(1,10), canvas]])

        t = Table(story)
        t.setStyle(TableStyle([
                        ('INNERGRID', (0,0), (-1,-1), 0.1, colors.black), 
                        ('BOX', (0,0), (-1,-1), 0.1, colors.black), 
                        ]))
        return [t]


    def myFirstPage(self, canvas, doc): 
        Title = '   NetPyLab Report' 
        pageinfo = "platypus example" 
        canvas.saveState() 
        canvas.setFont('Times-Bold',16) 
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT-108, Title) 
        canvas.setFont('Times-Roman',9) 
        canvas.drawString(inch, 0.75 * inch, "First Page / %s" % pageinfo) 
        canvas.restoreState() 

    def myLaterPages(self, canvas, doc): 
        pageinfo = "   NetPyLab Report"
        canvas.saveState() 
        canvas.setFont('Times-Roman',9) 
        canvas.drawString(inch, 0.75 * inch, "Page %d %s" % (doc.page, pageinfo)) 
        canvas.restoreState()

    def save(self):
        # self.draw_travels()
        # self.draw_verticals()
        # self.draw_timeline()
        # self.draw_legend()
        
        doc = SimpleDocTemplate(self.file) 
        Story = [Spacer(1,2*inch)] 
        style = styles["Normal"]
        Story.extend(self.draw_interface_history())
        Story.append(self.legend)
        Story.append(self.sequence_diagram)
        
        Story.extend(self.draw_packet_history())
        # Story.extend(self.draw_hex())

        x1, y1, x2, y2 =self.sequence_diagram.getBounds()
        width, height = x2-x1, y2-y1
        scale = min(PAGE_WIDTH*0.80 / (x2-x1), PAGE_HEIGHT*0.80/(y2-y1))
        
        self.sequence_diagram.shift(0, height * scale)
        self.sequence_diagram.height = height*scale
        self.sequence_diagram.scale(scale, scale)
        
        print 'Building Report'
        doc.build(Story, onFirstPage=self.myFirstPage, onLaterPages=self.myLaterPages)
