import pygame, random, sys, time, math, pickle, array as _arr

pygame.init()

# =============================================================================
#  WINDOW / CONSTANTS
# =============================================================================
W, H    = 1300, 840
CARD_W  = 88
CARD_H  = 126
FPS     = 60

C_GREEN1 = ( 16,  96,  16)
C_GREEN2 = ( 26, 136,  26)
C_WHITE  = (255, 255, 255)
C_BLACK  = (  0,   0,   0)
C_CREAM  = (255, 252, 228)
C_RED    = (208,  28,  28)
C_DKRED  = (120,   8,   8)
C_CRIM   = (155,   0,  18)
C_GOLD   = (255, 208,   0)
C_GYEL   = (255, 255,  90)
C_GGRN   = (  0, 220, 110)
C_GREY   = (170, 170, 170)
C_SLOT   = (255, 216,  48)
C_NAVY   = ( 20,  40, 100)
C_BLUE   = ( 40,  80, 200)
C_LBLUE  = ( 80, 140, 255)

SUITS  = ["H", "D", "C", "S"]
SYM    = {"H":"♥","D":"♦","C":"♣","S":"♠"}
RANKS  = list(range(1, 14))

def is_red(s): return s in ("H","D")
def rlbl(r):   return {1:"A",11:"J",12:"Q",13:"K"}.get(r,str(r))

# Layout
STOCK_X, STOCK_Y = 30, 60
WASTE_X, WASTE_Y = 148, 60
FOUND_Y          = 60
FOUND_XS         = [580 + i*112 for i in range(4)]
TAB_Y            = 230
TAB_XS           = [30 + i*154 for i in range(7)]
STEP_DOWN        = 18
STEP_UP          = 28

# =============================================================================
#  FONTS
# =============================================================================
Fsm  = pygame.font.SysFont("Georgia", 16)
Fmd  = pygame.font.SysFont("Georgia", 20, bold=True)
Flg  = pygame.font.SysFont("Georgia", 28, bold=True)
Fxl  = pygame.font.SysFont("Georgia", 52, bold=True)
Fsym = pygame.font.SysFont("Segoe UI Symbol", 24, bold=True)
Fhuge= pygame.font.SysFont("Georgia", 72, bold=True)

# =============================================================================
#  SOUND
# =============================================================================
try:
    pygame.mixer.init(44100,-16,1,512)
    def _tone(freq,dur,shape="sine",vol=0.28):
        sr=44100; n=int(sr*dur); buf=_arr.array('h',[0]*n)
        for i in range(n):
            t=i/sr; env=max(0.0,1.0-i/(n*0.85))
            if   shape=="sine":   v=math.sin(2*math.pi*freq*t)
            elif shape=="tri":    v=2*abs(2*(t*freq-math.floor(t*freq+0.5)))-1
            elif shape=="sq":     v=1.0 if math.sin(2*math.pi*freq*t)>0 else -1.0
            else:                 v=math.sin(2*math.pi*freq*t)
            buf[i]=int(32767*vol*env*v)
        return pygame.sndarray.make_sound(buf)
    SFX={
        "flip" :_tone(680, 0.07,"sine",0.26),
        "place":_tone(880, 0.09,"sine",0.30),
        "found":_tone(1100,0.13,"sine",0.36),
        "stock":_tone(480, 0.07,"tri", 0.22),
        "err"  :_tone(190, 0.10,"sq",  0.16),
        "w1"   :_tone(1047,0.18,"sine",0.40),
        "w2"   :_tone(1319,0.18,"sine",0.40),
        "w3"   :_tone(1568,0.22,"sine",0.46),
    }
    def sfx(n): SFX[n].play()
except Exception:
    def sfx(n): pass

# =============================================================================
#  PARTICLES
# =============================================================================
class Particle:
    __slots__=("x","y","vx","vy","life","tot","col","r")
    def __init__(self,x,y,col):
        a=random.uniform(0,math.tau); sp=random.uniform(2,5)
        self.x,self.y=float(x),float(y)
        self.vx,self.vy=math.cos(a)*sp,math.sin(a)*sp-random.uniform(1,3)
        self.tot=self.life=random.randint(28,55)
        self.col=col; self.r=random.randint(3,6)
    def tick(self):
        self.x+=self.vx; self.y+=self.vy
        self.vy+=0.2; self.vx*=0.96
        self.life-=1; return self.life>0
    def draw(self,s):
        r=max(1,int(self.r*self.life/self.tot))
        pygame.draw.circle(s,self.col,(int(self.x),int(self.y)),r)

PARTS=[]
def burst(x,y,col,n=18):
    for _ in range(n): PARTS.append(Particle(x,y,col))

# =============================================================================
#  BOUNCING WIN CARD
# =============================================================================
class BounceCard:
    """A card that flies around the screen bouncing off walls – classic win anim."""
    def __init__(self, suit, rank, x, y, delay):
        self.suit  = suit
        self.rank  = rank
        self.x     = float(x)
        self.y     = float(y)
        speed      = random.uniform(4, 9)
        angle      = random.uniform(0, math.tau)
        self.vx    = math.cos(angle) * speed
        self.vy    = math.sin(angle) * speed
        self.delay = delay   # frames before this card starts moving
        self.alive = True

    def update(self):
        if self.delay > 0:
            self.delay -= 1
            return
        self.x += self.vx
        self.y += self.vy
        # bounce off walls
        if self.x <= 0:
            self.x = 0; self.vx = abs(self.vx)
            burst(int(self.x), int(self.y)+CARD_H//2,
                  C_RED if is_red(self.suit) else C_GOLD, 6)
        if self.x >= W - CARD_W:
            self.x = W - CARD_W; self.vx = -abs(self.vx)
            burst(int(self.x)+CARD_W, int(self.y)+CARD_H//2,
                  C_RED if is_red(self.suit) else C_GOLD, 6)
        if self.y <= 0:
            self.y = 0; self.vy = abs(self.vy)
            burst(int(self.x)+CARD_W//2, int(self.y),
                  C_RED if is_red(self.suit) else C_GOLD, 6)
        if self.y >= H - CARD_H:
            self.y = H - CARD_H; self.vy = -abs(self.vy)
            burst(int(self.x)+CARD_W//2, int(self.y)+CARD_H,
                  C_RED if is_red(self.suit) else C_GOLD, 6)

    def draw(self, surf):
        # draw as a small card
        x, y = int(self.x), int(self.y)
        # shadow
        pygame.draw.rect(surf,(0,0,0,60),(x+4,y+4,CARD_W,CARD_H),border_radius=8)
        # face
        pygame.draw.rect(surf,C_CREAM,(x,y,CARD_W,CARD_H),border_radius=8)
        pygame.draw.rect(surf,C_BLACK,(x,y,CARD_W,CARD_H),2,border_radius=8)
        clr = C_RED if is_red(self.suit) else C_BLACK
        lbl = Fmd.render(rlbl(self.rank), True, clr)
        sm  = Fsym.render(SYM[self.suit], True, clr)
        surf.blit(lbl,(x+4,y+3))
        surf.blit(sm, (x+3,y+21))
        big = Fxl.render(SYM[self.suit], True, clr)
        surf.blit(big,(x+(CARD_W-big.get_width())//2,
                       y+(CARD_H-big.get_height())//2))

BOUNCE_CARDS = []   # filled when win triggers

def init_bounce_cards(g):
    """Launch all 52 cards bouncing around the screen."""
    global BOUNCE_CARDS
    BOUNCE_CARDS = []
    delay = 0
    for s in SUITS:
        for c in g.found[s]:
            bx = random.randint(0, W-CARD_W)
            by = random.randint(0, H-CARD_H)
            BOUNCE_CARDS.append(BounceCard(c.suit, c.rank, bx, by, delay))
            delay += 3   # stagger launch so they don't all appear at once

# =============================================================================
#  CARD
# =============================================================================
class Card:
    def __init__(self,suit,rank,face_up=False):
        self.suit=suit; self.rank=rank; self.face_up=face_up
        self.x=self.y=self.tx=self.ty=0.0

    def set_pos(self,x,y):
        self.x=self.tx=float(x); self.y=self.ty=float(y)

    def slide(self):
        self.x+=(self.tx-self.x)*0.22
        self.y+=(self.ty-self.y)*0.22

    def rect(self):
        return pygame.Rect(int(self.x),int(self.y),CARD_W,CARD_H)

    def _back(self,surf,x,y):
        pygame.draw.rect(surf,(0,0,0,50),(x+4,y+4,CARD_W,CARD_H),border_radius=9)
        pygame.draw.rect(surf,C_DKRED,(x,y,CARD_W,CARD_H),border_radius=9)
        for i in range(6):
            for j in range(9):
                px=x+8+i*13; py=y+9+j*12
                if x<px<x+CARD_W and y<py<y+CARD_H:
                    pygame.draw.circle(surf,C_CRIM,(px,py),2)
        pygame.draw.rect(surf,C_CRIM,(x+5,y+5,CARD_W-10,CARD_H-10),1,border_radius=6)
        pygame.draw.rect(surf,C_BLACK,(x,y,CARD_W,CARD_H),2,border_radius=9)

    def _face(self,surf,x,y):
        pygame.draw.rect(surf,(0,0,0,50),(x+4,y+4,CARD_W,CARD_H),border_radius=9)
        pygame.draw.rect(surf,C_CREAM,(x,y,CARD_W,CARD_H),border_radius=9)
        pygame.draw.rect(surf,C_BLACK,(x,y,CARD_W,CARD_H),2,border_radius=9)
        clr=C_RED if is_red(self.suit) else C_BLACK
        lbl=Fmd.render(rlbl(self.rank),True,clr)
        sm =Fsym.render(SYM[self.suit],True,clr)
        surf.blit(lbl,(x+4,y+3)); surf.blit(sm,(x+3,y+21))
        big=Fxl.render(SYM[self.suit],True,clr)
        surf.blit(big,(x+(CARD_W-big.get_width())//2,
                       y+(CARD_H-big.get_height())//2))
        l2=pygame.transform.rotate(Fmd.render(rlbl(self.rank),True,clr),180)
        s2=pygame.transform.rotate(Fsym.render(SYM[self.suit],True,clr),180)
        surf.blit(l2,(x+CARD_W-l2.get_width()-4,y+CARD_H-24))
        surf.blit(s2,(x+CARD_W-s2.get_width()-3,y+CARD_H-43))

    def draw(self,surf,glow=None):
        ix,iy=int(self.x),int(self.y)
        if glow=="yellow":
            pygame.draw.rect(surf,C_GYEL,(ix-4,iy-4,CARD_W+8,CARD_H+8),border_radius=11)
        elif glow=="green":
            pygame.draw.rect(surf,C_GGRN,(ix-4,iy-4,CARD_W+8,CARD_H+8),border_radius=11)
        if self.face_up: self._face(surf,ix,iy)
        else:            self._back(surf,ix,iy)

# =============================================================================
#  BACKGROUND
# =============================================================================
def make_bg():
    s=pygame.Surface((W,H))
    for y in range(H):
        t=y/H
        r=int(C_GREEN1[0]*(1-t)+C_GREEN2[0]*t)
        g=int(C_GREEN1[1]*(1-t)+C_GREEN2[1]*t)
        b=int(C_GREEN1[2]*(1-t)+C_GREEN2[2]*t)
        pygame.draw.line(s,(r,g,b),(0,y),(W,y))
    rng=random.Random(77)
    for _ in range(22000):
        px=rng.randint(0,W-1); py=rng.randint(0,H-1); v=rng.randint(-13,13)
        c=s.get_at((px,py))
        s.set_at((px,py),(max(0,min(255,c[0]+v)),
                          max(0,min(255,c[1]+v)),
                          max(0,min(255,c[2]+v))))
    return s
BG=make_bg()

# =============================================================================
#  MENU BACKGROUND
# =============================================================================
def make_menu_bg():
    s=pygame.Surface((W,H))
    for y in range(H):
        t=y/H
        r=int(C_NAVY[0]*(1-t)+C_BLACK[0]*t)
        g=int(C_NAVY[1]*(1-t)+C_BLACK[1]*t)
        b=int(C_NAVY[2]*(1-t)+C_BLACK[2]*t)
        pygame.draw.line(s,(r,g,b),(0,y),(W,y))
    rng=random.Random(42)
    for _ in range(120):
        x=rng.randint(0,W-1); y=rng.randint(0,H-1)
        r=rng.randint(1,3)
        brightness=rng.randint(150,255)
        pygame.draw.circle(s,(brightness,brightness,brightness),(x,y),r)
    return s
MENU_BG=make_menu_bg()

# =============================================================================
#  GAME STATE
# =============================================================================
class Game:
    def __init__(self, draw_count=1):
        self.draw_count = draw_count
        self.reset()

    def reset(self):
        deck=[Card(s,r) for s in SUITS for r in RANKS]
        random.shuffle(deck)
        self.tab=[[] for _ in range(7)]
        for i in range(7):
            for j in range(i+1):
                c=deck.pop()
                c.face_up=(j==i)
                self.tab[i].append(c)
            for j,c in enumerate(self.tab[i]):
                c.set_pos(TAB_XS[i], self._col_y(i,j))
        self.stock=deck
        self.waste=[]
        for c in self.stock: c.set_pos(STOCK_X,STOCK_Y)
        self.found={s:[] for s in SUITS}
        self.drag_cards=[]; self.drag_src=None; self.drag_off=(0,0)
        self.score=0; self.moves=0
        self.start=time.time()
        self.won=False; self.win_t=0
        self.hint_card=None; self.hint_t=0
        self.undo_stack=[]

    def _col_y(self,ci,ji):
        y=TAB_Y
        for j in range(ji):
            y+=STEP_DOWN if not self.tab[ci][j].face_up else STEP_UP
        return y

    def is_dragging(self,c): return c in self.drag_cards

    def set_targets(self):
        for c in self.stock: c.tx,c.ty=STOCK_X,STOCK_Y
        nw=len(self.waste)
        for k,c in enumerate(self.waste):
            d=nw-1-k
            if d>2: c.tx,c.ty=WASTE_X,WASTE_Y
            else:   c.tx,c.ty=WASTE_X+(2-d)*22,WASTE_Y
        for i,s in enumerate(SUITS):
            for c in self.found[s]: c.tx,c.ty=FOUND_XS[i],FOUND_Y
        for i,col in enumerate(self.tab):
            for j,c in enumerate(col):
                c.tx=TAB_XS[i]; c.ty=self._col_y(i,j)

    def slide_all(self):
        for c in self.stock:
            if not self.is_dragging(c): c.slide()
        for c in self.waste:
            if not self.is_dragging(c): c.slide()
        for s in SUITS:
            for c in self.found[s]:
                if not self.is_dragging(c): c.slide()
        for col in self.tab:
            for c in col:
                if not self.is_dragging(c): c.slide()

    def snapshot(self):
        self.undo_stack.append({
            "tab"  :[list(col) for col in self.tab],
            "stock":list(self.stock),
            "waste":list(self.waste),
            "found":{s:list(p) for s,p in self.found.items()},
            "score":self.score,"moves":self.moves,
        })
        if len(self.undo_stack)>60: self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack: sfx("err"); return
        snap=self.undo_stack.pop()
        self.tab=snap["tab"]; self.stock=snap["stock"]
        self.waste=snap["waste"]; self.found=snap["found"]
        self.score=snap["score"]; self.moves=snap["moves"]
        self.drag_cards=[]; self.drag_src=None
        sfx("flip")

    def save(self):
        try:
            with open("sol.dat","wb") as f: pickle.dump(self,f)
        except: pass

    @staticmethod
    def load():
        try:
            with open("sol.dat","rb") as f: return pickle.load(f)
        except: return None

# =============================================================================
#  RULES
# =============================================================================
def ok_tab(card,pile):
    if not pile: return card.rank==13
    t=pile[-1]
    return t.face_up and is_red(t.suit)!=is_red(card.suit) and t.rank==card.rank+1

def ok_found(card,pile):
    if not pile: return card.rank==1
    t=pile[-1]
    return t.suit==card.suit and t.rank==card.rank-1   # pile top must be one BELOW card

# =============================================================================
#  WIN CHECK
# =============================================================================
def check_win(g):
    if all(len(g.found[s])==13 for s in SUITS):
        g.won=True; g.win_t=0
        init_bounce_cards(g)
        pygame.time.set_timer(pygame.USEREVENT+1,220)

# =============================================================================
#  EXPOSE TOP
# =============================================================================
def expose_top(g,ci):
    col=g.tab[ci]
    if col and not col[-1].face_up:
        col[-1].face_up=True; g.score+=5
        burst(TAB_XS[ci]+CARD_W//2,col[-1].y+CARD_H//2,C_GYEL,10)
        sfx("flip")

# =============================================================================
#  PULL FROM SOURCE  (called only after confirmed valid drop)
# =============================================================================
def pull(g):
    src=g.drag_src
    if src is None: return
    kind=src[0]
    if kind=="waste":
        if g.waste and g.waste[-1] is g.drag_cards[0]:
            g.waste.pop()
    elif kind=="tab":
        col=g.tab[src[1]]
        if g.drag_cards and g.drag_cards[0] in col:
            del col[col.index(g.drag_cards[0]):]
            expose_top(g,src[1])
    elif kind=="found":
        s=src[1]
        if g.found[s] and g.found[s][-1] is g.drag_cards[0]:
            g.found[s].pop()

# =============================================================================
#  DOUBLE-CLICK DETECTOR
# =============================================================================
_dlp=(0,0); _dlt=0.0
def is_dbl(pos):
    global _dlp,_dlt
    now=time.time()
    ok=(now-_dlt<0.40 and math.hypot(pos[0]-_dlp[0],pos[1]-_dlp[1])<14)
    _dlp=pos; _dlt=now; return ok

# =============================================================================
#  AUTO-SEND TO FOUNDATION  (double-click)
# =============================================================================
def auto_found(g,pos):
    if g.waste:
        c=g.waste[-1]
        if c.rect().collidepoint(pos) and ok_found(c,g.found[c.suit]):
            g.snapshot(); g.waste.pop()
            fi=SUITS.index(c.suit)
            g.found[c.suit].append(c)
            c.tx,c.ty=FOUND_XS[fi],FOUND_Y
            g.score+=10; g.moves+=1
            burst(FOUND_XS[fi]+CARD_W//2,FOUND_Y+CARD_H//2,C_GOLD,22)
            sfx("found"); check_win(g); return True
    for i,col in enumerate(g.tab):
        if not col: continue
        c=col[-1]
        if not c.face_up: continue
        if c.rect().collidepoint(pos) and ok_found(c,g.found[c.suit]):
            g.snapshot(); col.pop(); expose_top(g,i)
            fi=SUITS.index(c.suit)
            g.found[c.suit].append(c)
            c.tx,c.ty=FOUND_XS[fi],FOUND_Y
            g.score+=10; g.moves+=1
            burst(FOUND_XS[fi]+CARD_W//2,FOUND_Y+CARD_H//2,C_GOLD,22)
            sfx("found"); check_win(g); return True
    return False

# =============================================================================
#  MOUSE DOWN
# =============================================================================
def col_y_now(g,ci,ji):
    y=TAB_Y
    for j in range(ji):
        y+=STEP_DOWN if not g.tab[ci][j].face_up else STEP_UP
    return y

def on_down(g,pos):
    mx,my=pos

    # stock
    if pygame.Rect(STOCK_X,STOCK_Y,CARD_W,CARD_H).collidepoint(pos):
        g.snapshot()
        if g.stock:
            n=min(g.draw_count,len(g.stock))
            for _ in range(n):
                c=g.stock.pop(); c.face_up=True
                c.x,c.y=STOCK_X,STOCK_Y
                g.waste.append(c)
            g.moves+=1; sfx("stock")
        else:
            while g.waste:
                c=g.waste.pop(); c.face_up=False; g.stock.append(c)
            g.score=max(0,g.score-20); sfx("stock")
        return

    # waste top
    if g.waste and not g.drag_cards:
        c=g.waste[-1]
        if c.rect().collidepoint(pos):
            g.drag_cards=[c]; g.drag_src=("waste",)
            g.drag_off=(mx-int(c.x),my-int(c.y)); return

    # foundation top
    if not g.drag_cards:
        for i,s in enumerate(SUITS):
            if g.found[s]:
                c=g.found[s][-1]
                if pygame.Rect(FOUND_XS[i],FOUND_Y,CARD_W,CARD_H).collidepoint(pos):
                    g.drag_cards=[c]; g.drag_src=("found",s)
                    g.drag_off=(mx-int(c.x),my-int(c.y)); return

    # tableau
    if not g.drag_cards:
        for i in range(6,-1,-1):
            col=g.tab[i]
            if not col: continue
            for j in range(len(col)-1,-1,-1):
                c=col[j]; cy=col_y_now(g,i,j)
                vis=max(12,col_y_now(g,i,j+1)-cy) if j<len(col)-1 else CARD_H
                if not pygame.Rect(TAB_XS[i],cy,CARD_W,vis).collidepoint(pos): continue
                if not c.face_up:
                    if j==len(col)-1:
                        g.snapshot(); c.face_up=True; g.score+=5; g.moves+=1
                        burst(TAB_XS[i]+CARD_W//2,cy+CARD_H//2,C_GYEL,10); sfx("flip")
                    return
                g.drag_cards=col[j:]; g.drag_src=("tab",i)
                g.drag_off=(mx-int(c.x),my-int(c.y)); return

# =============================================================================
#  MOUSE UP
# =============================================================================
def on_up(g,pos):
    if not g.drag_cards: return
    top=g.drag_cards[0]; mx,my=pos

    # foundation
    if len(g.drag_cards)==1:
        for i,s in enumerate(SUITS):
            if (pygame.Rect(FOUND_XS[i],FOUND_Y,CARD_W,CARD_H).collidepoint(pos)
                    and ok_found(top,g.found[s])):
                g.snapshot(); pull(g)
                g.found[s].append(top)
                top.tx,top.ty=FOUND_XS[i],FOUND_Y
                g.score+=10; g.moves+=1
                burst(FOUND_XS[i]+CARD_W//2,FOUND_Y+CARD_H//2,C_GOLD,24)
                sfx("found"); check_win(g)
                g.drag_cards=[]; g.drag_src=None; return

    # tableau
    best=-1
    for i in range(7):
        if not pygame.Rect(TAB_XS[i]-12,TAB_Y-12,CARD_W+24,H).collidepoint(pos): continue
        if not ok_tab(top,g.tab[i]): continue
        if g.drag_src[0]=="tab" and g.drag_src[1]==i and g.tab[i]: continue
        if best==-1: best=i
        elif abs(mx-(TAB_XS[i]+CARD_W//2))<abs(mx-(TAB_XS[best]+CARD_W//2)): best=i
    if best!=-1:
        cards=list(g.drag_cards); g.snapshot(); pull(g)
        for c in cards: g.tab[best].append(c)
        g.score+=5; g.moves+=1; sfx("place")
        g.drag_cards=[]; g.drag_src=None; return

    sfx("err"); g.drag_cards=[]; g.drag_src=None

# =============================================================================
#  HINT
# =============================================================================
def hint(g):
    for col in g.tab:
        if col and col[-1].face_up and ok_found(col[-1],g.found[col[-1].suit]):
            g.hint_card=col[-1]; g.hint_t=120; return
    if g.waste and ok_found(g.waste[-1],g.found[g.waste[-1].suit]):
        g.hint_card=g.waste[-1]; g.hint_t=120; return
    if g.waste:
        wc=g.waste[-1]
        for col in g.tab:
            if ok_tab(wc,col): g.hint_card=wc; g.hint_t=120; return
    for i,src in enumerate(g.tab):
        for j,c in enumerate(src):
            if not c.face_up: continue
            for k,dst in enumerate(g.tab):
                if k==i: continue
                if ok_tab(c,dst): g.hint_card=c; g.hint_t=120; return
    g.hint_card=None; g.hint_t=0

# =============================================================================
#  AUTO COMPLETE
# =============================================================================
def auto_complete(g):
    moved=True
    while moved:
        moved=False
        if g.waste:
            c=g.waste[-1]
            if ok_found(c,g.found[c.suit]):
                g.waste.pop(); g.found[c.suit].append(c)
                g.score+=10; sfx("found"); moved=True; check_win(g)
        for i,col in enumerate(g.tab):
            if not col: continue
            c=col[-1]
            if c.face_up and ok_found(c,g.found[c.suit]):
                col.pop(); expose_top(g,i)
                g.found[c.suit].append(c)
                g.score+=10; sfx("found"); moved=True; check_win(g)

# =============================================================================
#  DRAW HELPERS
# =============================================================================
def draw_slot(surf,x,y,lbl=""):
    pygame.draw.rect(surf,(0,0,0,35),(x+3,y+3,CARD_W,CARD_H),border_radius=9)
    pygame.draw.rect(surf,C_SLOT,(x,y,CARD_W,CARD_H),2,border_radius=9)
    if lbl:
        t=Fsym.render(lbl,True,(*C_SLOT[:3],120))
        surf.blit(t,(x+(CARD_W-t.get_width())//2,y+(CARD_H-t.get_height())//2))

def draw_button(surf,x,y,w,h,text,hover=False,selected=False):
    if selected:
        col=(60,180,60); border=C_GOLD
    elif hover:
        col=(60,100,200); border=C_WHITE
    else:
        col=(30,60,150); border=C_LBLUE
    pygame.draw.rect(surf,col,(x,y,w,h),border_radius=12)
    pygame.draw.rect(surf,border,(x,y,w,h),3,border_radius=12)
    t=Flg.render(text,True,C_WHITE)
    surf.blit(t,(x+(w-t.get_width())//2,y+(h-t.get_height())//2))

# =============================================================================
#  MENU SCREEN
# =============================================================================
def run_menu(screen,clock):
    """Show draw-mode selection. Returns 1 or 3."""
    mx=my=0
    while True:
        mx,my=pygame.mouse.get_pos()
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                if pygame.Rect(W//2-220,450,200,70).collidepoint(ev.pos): return 1
                if pygame.Rect(W//2+ 20,450,200,70).collidepoint(ev.pos): return 3

        screen.blit(MENU_BG,(0,0))

        # title
        t=Fhuge.render("SOLITAIRE",True,C_GOLD)
        screen.blit(t,(W//2-t.get_width()//2,130))
        sub=Flg.render("Classic Klondike",True,C_GREY)
        screen.blit(sub,(W//2-sub.get_width()//2,215))

        # ── coded by credit ──────────────────────────────────────────────────
        credit=Fsm.render("coded by @non G00nz",True,(139,115,35))
        screen.blit(credit,(W//2-credit.get_width()//2,252))

        # decorative suits
        for k,(sym,col,ox) in enumerate([("♠",C_WHITE,-300),("♥",C_RED,-150),
                                          ("♦",C_RED,150),("♣",C_WHITE,300)]):
            s=Fhuge.render(sym,True,(*col[:3],80))
            screen.blit(s,(W//2+ox-s.get_width()//2,310))

        # prompt
        p=Fmd.render("Choose Draw Mode",True,C_WHITE)
        screen.blit(p,(W//2-p.get_width()//2,408))

        h1=pygame.Rect(W//2-220,450,200,70).collidepoint(mx,my)
        h3=pygame.Rect(W//2+ 20,450,200,70).collidepoint(mx,my)
        draw_button(screen,W//2-220,450,200,70,"Draw 1",hover=h1)
        draw_button(screen,W//2+ 20,450,200,70,"Draw 3",hover=h3)

        d1=Fsm.render("Turn 1 card at a time",True,C_GREY)
        d3=Fsm.render("Turn 3 cards at a time",True,C_GREY)
        screen.blit(d1,(W//2-220+(200-d1.get_width())//2,528))
        screen.blit(d3,(W//2+ 20+(200-d3.get_width())//2,528))

        # card decorations
        for k,suit in enumerate(SUITS):
            clr=C_RED if is_red(suit) else C_WHITE
            bx=50+k*60; by=H-120
            pygame.draw.rect(screen,C_CREAM,(bx,by,44,63),border_radius=5)
            pygame.draw.rect(screen,C_BLACK,(bx,by,44,63),2,border_radius=5)
            s=Fsym.render(SYM[suit],True,clr)
            screen.blit(s,(bx+(44-s.get_width())//2,by+(63-s.get_height())//2))

        pygame.display.flip()
        clock.tick(FPS)

# =============================================================================
#  RENDER GAME
# =============================================================================
def render(g,screen,mouse):
    global PARTS
    screen.blit(BG,(0,0))

    # top bar
    bar=pygame.Surface((W,48),pygame.SRCALPHA); bar.fill((0,0,0,145))
    screen.blit(bar,(0,0))
    t=int(time.time()-g.start); mm,ss=divmod(t,60)
    screen.blit(Fsm.render(f"⏱ {mm:02d}:{ss:02d}",True,C_WHITE),(12,15))
    screen.blit(Fsm.render(f"★ {g.score}",True,C_GOLD),(145,15))
    screen.blit(Fsm.render(f"♻ {g.moves} moves",True,C_GREY),(255,15))
    dc=f"Draw {g.draw_count}"
    screen.blit(Fsm.render(dc,True,C_LBLUE),(390,15))
    screen.blit(Fsm.render("[R] New  [M] Menu  [U] Undo  [H] Hint  [A] Auto  [S] Save  [L] Load  | Dbl-click→Found",
                           True,C_GREY),(460,15))

    # stock
    if g.stock:
        for k in range(min(3,len(g.stock))):
            pygame.draw.rect(screen,C_DKRED,(STOCK_X-k,STOCK_Y-k,CARD_W,CARD_H),border_radius=9)
        arr=Flg.render("↻",True,C_WHITE)
        screen.blit(arr,(STOCK_X+(CARD_W-arr.get_width())//2,
                         STOCK_Y+(CARD_H-arr.get_height())//2))
        pygame.draw.rect(screen,C_BLACK,(STOCK_X,STOCK_Y,CARD_W,CARD_H),2,border_radius=9)
    else:
        draw_slot(screen,STOCK_X,STOCK_Y,"↻")

    # waste (fan of up to 3)
    if not g.waste: draw_slot(screen,WASTE_X,WASTE_Y)
    else:
        show=g.waste[-3:]
        for k,c in enumerate(show):
            is_top=(k==len(show)-1)
            if not g.is_dragging(c):
                c.draw(screen,glow=("yellow" if is_top and not g.drag_cards else None))

    # foundations
    for i,s in enumerate(SUITS):
        fx,fy=FOUND_XS[i],FOUND_Y
        if not g.found[s]: draw_slot(screen,fx,fy,SYM[s])
        else:
            for c in g.found[s]:
                if not g.is_dragging(c): c.draw(screen)

    # tableau
    for i,col in enumerate(g.tab):
        if not col: draw_slot(screen,TAB_XS[i],TAB_Y,"K")
        else:
            for j,c in enumerate(col):
                if not g.is_dragging(c):
                    gl="green" if (c is g.hint_card and g.hint_t>0) else None
                    c.draw(screen,glow=gl)

    # dragged cards
    mx,my=mouse; ox,oy=g.drag_off
    for k,c in enumerate(g.drag_cards):
        c.x=mx-ox; c.y=my-oy+k*STEP_UP
        c.draw(screen,glow="yellow")

    # particles
    PARTS=[p for p in PARTS if p.tick()]
    for p in PARTS: p.draw(screen)

    # hint countdown
    if g.hint_t>0:
        g.hint_t-=1
        if g.hint_t==0: g.hint_card=None

    # ── WIN ANIMATION ─────────────────────────────────────────────────────────
    if g.won:
        g.win_t+=1

        # dark overlay (fades in quickly)
        ov=pygame.Surface((W,H),pygame.SRCALPHA)
        ov.fill((0,0,0,min(160,g.win_t*4)))
        screen.blit(ov,(0,0))

        # update + draw all bouncing cards
        for bc in BOUNCE_CARDS:
            bc.update()
            bc.draw(screen)

        # particles from bounces
        PARTS=[p for p in PARTS if p.tick()]
        for p in PARTS: p.draw(screen)

        # "YOU WIN!" text pulsing on top
        pulse=1.0+0.06*math.sin(g.win_t*0.10)
        base=Fhuge.render("YOU WIN!",True,C_GOLD)
        bw=int(base.get_width()*pulse); bh=int(base.get_height()*pulse)
        scaled=pygame.transform.smoothscale(base,(max(1,bw),max(1,bh)))
        # semi-transparent backing
        backing=pygame.Surface((bw+40,bh+20),pygame.SRCALPHA)
        backing.fill((0,0,0,160))
        screen.blit(backing,(W//2-bw//2-20,H//2-bh//2-65))
        screen.blit(scaled,(W//2-bw//2,H//2-bh//2-60))

        info=Flg.render(f"Score: {g.score}   Time: {mm:02d}:{ss:02d}   Moves: {g.moves}",
                        True,C_WHITE)
        ib=pygame.Surface((info.get_width()+30,info.get_height()+10),pygame.SRCALPHA)
        ib.fill((0,0,0,150))
        screen.blit(ib,(W//2-info.get_width()//2-15,H//2+bh//2-35))
        screen.blit(info,(W//2-info.get_width()//2,H//2+bh//2-30))

        note=Fsm.render("Press R to play again  |  Press M for menu",True,C_GREY)
        screen.blit(note,(W//2-note.get_width()//2,H//2+bh//2+18))

# =============================================================================
#  MAIN LOOP
# =============================================================================
screen=pygame.display.set_mode((W,H))
pygame.display.set_caption("Solitaire Deluxe")
clock=pygame.time.Clock()

_wseq=["w1","w2","w3"]; _widx=0

def new_game(draw_count):
    global g, PARTS, _widx, BOUNCE_CARDS
    g=Game(draw_count); PARTS.clear(); BOUNCE_CARDS=[]; _widx=0

# show menu first
draw_choice=run_menu(screen,clock)
g=Game(draw_choice)

while True:
    mouse=pygame.mouse.get_pos()

    for ev in pygame.event.get():
        if ev.type==pygame.QUIT:
            pygame.quit(); sys.exit()

        if ev.type==pygame.USEREVENT+1:
            if _widx<len(_wseq): sfx(_wseq[_widx]); _widx+=1
            else: pygame.time.set_timer(pygame.USEREVENT+1,0); _widx=0

        if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
            if not g.won:
                if is_dbl(ev.pos):
                    if auto_found(g,ev.pos): continue
                on_down(g,ev.pos)

        if ev.type==pygame.MOUSEBUTTONUP and ev.button==1:
            if not g.won:
                on_up(g,ev.pos)

        if ev.type==pygame.KEYDOWN:
            k=ev.key
            if k==pygame.K_r:
                new_game(g.draw_count)
            if k==pygame.K_m:
                dc=run_menu(screen,clock)
                new_game(dc)
            if k==pygame.K_u and not g.won: g.undo()
            if k==pygame.K_h and not g.won: hint(g)
            if k==pygame.K_a and not g.won: auto_complete(g)
            if k==pygame.K_s: g.save(); sfx("stock")
            if k==pygame.K_l:
                loaded=Game.load()
                if loaded:
                    g=loaded; PARTS.clear(); BOUNCE_CARDS=[]

    if not g.won:
        g.set_targets()
        g.slide_all()

    render(g,screen,mouse)
    pygame.display.flip()
    clock.tick(FPS)
