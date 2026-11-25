import json,re,difflib,collections,sys
sys.path.insert(0,'/tmp')
exec(open('/tmp/match.py').read().split('names=set()')[0])
W='patch/calcio-storico/_work/'
OVR={ # name in source -> (codice,nome) or None to skip
 'L M E':('030062','A.S.D. Lavarian Mortean Esperia (LME)'),
 'A.S.D. COMUNALE FIUME V. BANNIA':('093021','A.S.D. Fiume Veneto Bannia'),
 'A.S.D. TORRE':('093033','A.S.D. Torre'),'TORRE':None,
 'A.S.D. TORRE (Campolongo)':('030138','A.S.D. Torre'),
 'A.S.D. ZAULE RABUIESE':('032003','A.S.D. Muggia 1967'),'Zaule Rabuiese':('032003','A.S.D. Muggia 1967'),
 'Torreanese':None,'TORREANESE':None,'A.S.D. MUGGIA 2020':None,'MUGGIA 2020':None,'A.S.D. MUGLIA F.':None,'MUGLIA F.':None,
 'Isontina':None,'Bisiaca':None,'BISIACA':None,'Romana Monfalcone':None,'ROMANA MONFALCONE':None,
 'A.S.D. VIRTUS CORNO':None,'VIRTUS CORNO':None,'Virtus Corno':None,
}
# Promozione 2023/24 'TORRE' is Pordenone, Seconda F 2023/24 'TORRE' is Campolongo: handled by context
CTX={('2023/24','Promozione FVG, girone A','TORRE'):('093033','A.S.D. Torre'),('2023/24','Seconda Categoria, girone F','TORRE'):('030138','A.S.D. Torre')}
COME={('032003','A.S.D. Muggia 1967'):'Zaule Rabuiese',('030023','A.S.D. Pro Cervignano Ruda'):'Pro Cervignano Muscoli'}
idx={(x['codice'],x['nome']):x for x in C}
def resolve(stag,camp,n):
    if (stag,camp,n) in CTX: return idx[CTX[(stag,camp,n)]]
    if n in OVR: return idx[OVR[n]] if OVR[n] else None
    b,s=match(n)
    return b if s>=0.78 else None
OUT={ # (stagione, codice, nome) -> pos override for organico seasons
 ('2023/24','030049','A.S.D. Brian Lignano Calcio'):'1 (promossa in Serie D)',
 ('2023/24','032001','A.S.D. Sistiana-Sesljan'):'retrocessa',
 ('2023/24','030127','A.S.D. Tricesimo Calcio'):'retrocessa',
 ('2023/24','093018','A.S.D. S.P.A.L. Cordovado'):'retrocessa',
 ('2023/24','093022','A.S.D. Comunale Fontanafredda'):'1 (promossa)',
 ('2023/24','031012','A.S.D. U. Fincantieri Monfalcone'):'1 (promossa)',
 ('2023/24','032002','A.S.D. N.K. Kras Repen'):'promossa (vincitrice play-off)',
 ('2023/24','093010','S.A.S. Casarsa'):'finalista play-off (poi ripescata in Eccellenza)',
 ('2021/22','030043','A.S.D. Gemonese'):'retrocessa',('2021/22','093022','A.S.D. Comunale Fontanafredda'):'retrocessa',
 ('2021/22','030095',"A.S.D. Rive d'Arcano Flaibano"):'retrocessa',('2021/22','030129','A.S.D. Ancona Lumignacco'):'retrocessa',
 ('2021/22','031016','A.S.D. Ronchi Calcio'):'retrocessa',('2021/22','032006','A.S.D. Primorec'):'retrocessa',
 ('2024/25','032006','A.S.D. San Luigi Calcio'):'promossa in Serie D',
}
EXTRA=[ # (stagione,codice,nome,campionato,pos,fonte)
 ('2021/22','030026','A.S.D. Forum Julii Calcio','Promozione FVG','promossa in Eccellenza','organico'),
 ('2021/22','031007','A.S.D. Juventina S. Andrea','Promozione FVG','promossa in Eccellenza','organico'),
 ('2024/25','030026','A.S.D. Forum Julii Calcio','Promozione FVG','promossa in Eccellenza','organico'),
 ('2024/25','030062','A.S.D. Lavarian Mortean Esperia (LME)','Promozione FVG','promossa in Eccellenza','organico'),
]
F={'2022/23':'LND FVG, Classifiche Ufficiali 2022/23 (all. CU 103 Del. Trieste)',
   '2023/24':'LND FVG CU 14 2023/24 (calendari); Wikipedia it Eccellenza FVG 2023-24 e 2024-25',
   '2021/22':'Wikipedia it Eccellenza FVG 2021-22; organici 2022/23 (LND FVG Classifiche Ufficiali 2022/23)',
   '2024/25':'Wikipedia it Eccellenza FVG 2024-25; LND FVG Del. Trieste CU 92 2025/26 (elenco Eccellenza 2025/26)',
   '2025/26':'LND FVG Del. Trieste CU 92 2025/26 (graduatorie Eccellenza/Promozione 2025/26)'}
rec={} # (codice,nome)->{stagione:(camp,pos)}, fonti
fonti=collections.defaultdict(set)
def put(x,stag,camp,pos,fonte):
    k=(x['codice'],x['nome'])
    c=camp+(f" (come {COME[(x['codice'],x['nome'])]})" if (x['codice'],x['nome']) in COME and stag<'2024/25' else '')
    rec.setdefault(k,{})[stag]=(c,pos); fonti[k].add(fonte)
for line in open(W+'2022-23.txt'):
    line=line.strip()
    if line.startswith('##'): stag,camp=line[3:].split('|'); i=0; continue
    if not line: continue
    i+=1; p=line.split('|'); x=resolve(stag,camp,p[0])
    if x: put(x,stag,camp,p[2] if len(p)>2 else i,F[stag])
for line in open(W+'2023-24-organico.txt'):
    line=line.strip()
    if line.startswith('##'): stag,camp=line[3:].split('|'); continue
    for n in line.split(';'):
        x=resolve(stag,camp,n.strip())
        if not x: print('skip',stag,n); continue
        put(x,stag,camp,OUT.get((stag,x['codice'],x['nome']),'n.d.'),F[stag])
for stag,cod,nome,camp,pos,_ in EXTRA:
    put(idx[(cod,nome)],stag,camp,pos,F[stag])
# merge rules vs existing
bycod=collections.defaultdict(list); n_upd=0; n_ent=0
for k,seas in rec.items():
    x=idx[k]; old={s['stagione']:s for s in x['storico']}
    st=[]
    for s,(camp,pos) in sorted(seas.items()):
        o=old.get(s)
        if o and o['pos'] not in ('n.d.',None,'') and (pos=='n.d.' or not isinstance(pos,int)): continue
        if o and pos=='n.d.' and o['campionato'].lower().startswith(camp.split(',')[0].lower()) and ',' not in camp: continue
        st.append({'stagione':s,'campionato':camp,'pos':pos})
    if not st: continue
    n_upd+=1; n_ent+=len(st)
    bycod[x['codice']].append({'codice':x['codice'],'comune':x['comune'],'prov':x['prov'],'nome':x['nome'],'sport':'calcio','storico':st,'fonte':'; '.join(sorted(fonti[k]))})
for cod,arr in bycod.items():
    json.dump(arr,open(f'patch/calcio-storico/{cod}.json','w'),ensure_ascii=False,indent=1)
print('societa',n_upd,'voci',n_ent,'file',len(bycod))
