"""Generate report illustrations and the complete compact relations appendix."""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor,white
import json,textwrap,re
R=Path(__file__).resolve().parents[1];D=R/'doc/report';M=json.loads((R/'src/dal/models/relational/dictionary.json').read_text())
c=canvas.Canvas(str(D/'architecture.pdf'),pagesize=(500,175))
boxes=[(8,90,145,65,'Presentation','Forms / search / result notices'),(178,90,145,65,'Application','HTTP + validation + transactions'),(348,90,145,65,'Data access','Bound SQL / FK-aware connection')]
for x,y,w,h,title,sub in boxes:
 c.setFillColor(HexColor('#e7f1f0'));c.setStrokeColor(HexColor('#236a67'));c.roundRect(x,y,w,h,6,fill=1,stroke=1);c.setFillColor(HexColor('#16343b'));c.setFont('Helvetica-Bold',11);c.drawCentredString(x+w/2,y+42,title);c.setFont('Helvetica',7);c.drawCentredString(x+w/2,y+22,sub)
for a,b in [(153,178),(323,348)]:
 c.line(a,122,b,122);c.line(b,122,b-5,125);c.line(b,122,b-5,119)
c.setFillColor(HexColor('#102f38'));c.roundRect(180,10,310,50,6,fill=1,stroke=0);c.setFillColor(white);c.setFont('Helvetica-Bold',11);c.drawCentredString(335,40,'SQLite · 34 relations · schema + seed + queries');c.setFont('Helvetica',8);c.drawCentredString(335,24,'Candidate keys / deferred FKs / integrity triggers / indexes');c.setStrokeColor(HexColor('#236a67'));c.line(420,90,420,60);c.line(420,60,417,65);c.line(420,60,423,65)
c.setFillColor(HexColor('#526d76'));c.setFont('Helvetica',8);c.drawString(10,35,'Request → validate → transaction → SQL');c.drawString(10,21,'Rows or errors return through the layers.');c.save()
# Honest interface schematic, not a browser screenshot.
c=canvas.Canvas(str(D/'ui-schematic.pdf'),pagesize=(500,140));c.setFillColor(HexColor('#f1f5f6'));c.rect(0,0,500,140,fill=1,stroke=0);c.setFillColor(HexColor('#102f38'));c.rect(0,0,110,140,fill=1,stroke=0);c.setFillColor(white);c.setFont('Helvetica-Bold',11);c.drawString(10,118,'Retail-Mesh');c.setFont('Helvetica',8)
for i,v in enumerate(['Customer journey','Provider metrics','Award ledger','34 relation forms']):c.drawString(10,96-i*18,v)
c.setFillColor(HexColor('#16343b'));c.setFont('Helvetica-Bold',12);c.drawString(125,118,'Provider');c.setFont('Helvetica',8);c.drawString(125,98,'Search any field     [Search]     [Add record]');c.setFillColor(white);c.rect(124,37,362,48,fill=1,stroke=0);c.setFillColor(HexColor('#16343b'));c.drawString(132,70,'Id     RegistrationJurisdiction     LegalName       Actions');c.drawString(132,50,'1      CA-BC                             Dealer A          Edit / Delete');c.setFont('Helvetica-Oblique',8);c.drawString(125,16,'Interface schematic; live browser screenshots still required.');c.save()
def esc(s):
 for a,b in [ ('\\','\\textbackslash{}'),('_','\\_'),('&','\\&'),('%','\\%'),('#','\\#')]:s=s.replace(a,b)
 return s
# Use \allowbreak between long identifiers at CamelCase boundaries for compact columns.
def code(s):return r'\texttt{'+re.sub(r'(?<=[a-z])(?=[A-Z])',r'\\allowbreak{}',esc(s))+r'}'
def field(c,opt=False):return code(c)+('?' if opt else '')
s=[r'\section*{Complete Relations and Constraints}',r'\fontsize{7}{8}\selectfont\raggedright',r'Every relation below also has \texttt{Id INTEGER PRIMARY KEY AUTOINCREMENT}. CK denotes mandatory UNIQUE business columns. A question mark marks a nullable column; all others are NOT NULL. All attributes ending in Id are FKs to the matching entity, except the exceptions below. References target Id; no deletion cascades. Full SQL and trigger conditions accompany this report.']
for t,m in M.items():
 s+=[r'\par\vspace{2.0pt}\noindent\textbf{'+esc(t)+r'}. '+', '.join(field(c,c in m['optional']) for c in m['fields'])+r'.\par\noindent CK: '+', '.join(code(c) for c in m['ck'])+'.']
 # All FK target names explicit through compact suffix mapping.
 exceptions=[]
 for col,target in m['fks'].items():
  if col!=target+'Id':exceptions.append(code(col)+r'$\to$'+code(target))
 if exceptions:s[-1]+=' FK exceptions: '+'; '.join(exceptions)+'.'
 if m['unique']:s[-1]+=' Other UQ: '+'; '.join('('+','.join(code(x) for x in u)+')' for u in m['unique'])+'.'
s+=[r'\par\vspace{4pt}\textbf{Shared domain and cross-row constraints.} Business CK values are immutable after insertion. Dates use YYYY-MM-DD, timestamps use canonical UTC. Valid/effective/active, activity and period end values must exceed their starts; NULL end is unbounded. Prices/charges/benefits are nonnegative; currencies are three uppercase letters when supplied. VIN is 17 permitted uppercase characters. Identity pairs have AccountAId $<$ AccountBId; Verified requires VerifiedAt and no revocation. Activity kind is Sale, Rental or Service; exactly one matching owned subtype is mandatory through bidirectional deferred composite FKs. Rental replacement service and purpose must be jointly present or absent. AssessmentBasis is Event or Period; results are Qualified or Rejected; award status is Issued or Cancelled. AcceptedEvaluationId is unique, qualified, and matches subject, rule and period; FirstComponentId forces at least one owned benefit. Overlapping authorization, enrollment and definition/version intervals are rejected. Evaluations and cited evidence sources are immutable. Evidence is append-only until acceptance, then frozen; identity snapshots must match a currently verified assertion. Program/authorization eligibility is retained for reviewer validation, not automatically certified.']
(D/'relations.tex').write_text('\n'.join(s)+'\n')
