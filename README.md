# Forensic Financial Statement Analysis

Runs a set of forensic accounting questions against a company's SEC 10-K and
produces a report where **every factual claim is backed by a quotation the tool
has mechanically verified against the filing**.

That verification is the point. The model is asked to supply verbatim
quotations supporting each figure it cites; the application then checks each
quotation appears character-for-character in the source text and marks any that
does not. A paraphrase, a reformatted number, or text stitched together from
two places is reported as unverified rather than presented as a finding.

It also compares the current filing against the prior year, which is where the
more interesting findings tend to come from — a disclosure that quietly
disappeared is not visible in either year's filing read alone.

## What it does

- Parses inline XBRL filings straight from an EDGAR download — no API calls,
  no scraping. Company identity comes from DEI tags rather than filenames.
- Locates the audit report, MD&A, and financial statements, and pins them in
  front of the full text.
- Asks each question in its own request, against one shared cached copy of the
  filing.
- Rates each finding on four anchored levels — `none`, `minor`, `material`,
  `severe` — and flags `material` and above.
- Writes a JSON record, a Markdown report, and a PDF.

## Setup

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
export ANTHROPIC_API_KEY='...'
```

The key is read from the environment and is never written to disk or read from
a file in this repository.

## Adding a filing

Download the complete XBRL folder for a filing from
[SEC EDGAR](https://www.sec.gov/edgar/searchedgar/companysearch) and drop it in
whole:

```
Latest 10k/0001652044-26-000018-xbrl/
Previous Year 10k/0001652044-25-000014-xbrl/
```

Filings are not committed to this repository — they are large, public, and
specific to whichever company you are looking at.

## Running

Check the question files parse before spending anything. This is free:

```bash
python scripts/check_questions.py
```

Then:

```bash
python scripts/run_analysis.py                  # every question set
python scripts/run_analysis.py --dry-run        # resolve everything, no API calls
python scripts/run_analysis.py --set mda        # one set
python scripts/run_analysis.py --only 1,6,13    # specific questions
```

Reports are written to `output/`.

## Questions

Question sets live in `Analysis Questions/` as plain `.txt` files, one folder
per set. They are ordinary numbered questions — edit them, or add your own set,
and the loader will pick it up. `check_questions.py` reports what the
application will actually see, which is worth running after any edit: several
of this project's early failures were formatting problems in the question
files rather than bugs in the code.

## Cost

Roughly **$12 per company** for 70 questions against a filing the size of
Alphabet's, on `claude-opus-5`. The dominant cost is not output — it is
re-reading the cached filing once per question, which is about half the bill.
A smaller filer costs proportionally less; context size drives most of it.

`--dry-run` resolves the filing, sections and questions without making a single
API call, which is the cheapest way to confirm a new company is set up
correctly.

## Reproducibility

Concern levels are produced by a language model and are **not perfectly
reproducible**. On a 1–10 scale, repeated runs of an identical filing disagreed
on 54% of questions; collapsing those same runs into the current four levels
cuts that to 31%, and the residual disagreement sits almost entirely on the
`none`/`minor` boundary, where neither level is flagged.

`scripts/measure_variance.py` measures this. `--baseline` analyses run records
already on disk and costs nothing:

```bash
python scripts/measure_variance.py --baseline
python scripts/measure_variance.py --set audit --runs 5
```

Treat the flagged findings and their verified quotations as the output. Treat
the levels as a triage aid, not a measurement.

## Layout

```
forensic/
  ixbrl.py       inline XBRL parsing, fact extraction, text rendering
  filing.py      filing discovery and identity from DEI tags
  sections.py    locating the audit report, MD&A, financial statements
  questions.py   parsing question files
  analysis.py    schemas, prompt, runner, evidence verification
  research.py    parsing the 100-step research workbook format
  report_pdf.py  PDF generation
  claude.py      the Anthropic API wrapper (caching, streaming, structured output)
scripts/
  run_analysis.py       the main entry point
  check_questions.py    validate question files (free)
  check_research.py     validate the research workbook (free)
  measure_variance.py   measure run-to-run reproducibility
  inspect_filings.py    inspect a parsed filing
```
%PDF-1.4
%���� ReportLab Generated PDF document (opensource)
1 0 obj
<<
/F1 2 0 R /F2 3 0 R /F3 6 0 R /F4 7 0 R
>>
endobj
2 0 obj
<<
/BaseFont /Helvetica /Encoding /WinAnsiEncoding /Name /F1 /Subtype /Type1 /Type /Font
>>
endobj
3 0 obj
<<
/BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding /Name /F2 /Subtype /Type1 /Type /Font
>>
endobj
4 0 obj
<<
/Contents 40 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
5 0 obj
<<
/Contents 41 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
6 0 obj
<<
/BaseFont /Helvetica-BoldOblique /Encoding /WinAnsiEncoding /Name /F3 /Subtype /Type1 /Type /Font
>>
endobj
7 0 obj
<<
/BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding /Name /F4 /Subtype /Type1 /Type /Font
>>
endobj
8 0 obj
<<
/Contents 42 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
9 0 obj
<<
/Contents 43 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
10 0 obj
<<
/Contents 44 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
11 0 obj
<<
/Contents 45 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
12 0 obj
<<
/Contents 46 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
13 0 obj
<<
/Contents 47 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
14 0 obj
<<
/Contents 48 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
15 0 obj
<<
/Contents 49 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
16 0 obj
<<
/Contents 50 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
17 0 obj
<<
/Contents 51 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
18 0 obj
<<
/Contents 52 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
19 0 obj
<<
/Contents 53 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
20 0 obj
<<
/Contents 54 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
21 0 obj
<<
/Contents 55 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
22 0 obj
<<
/Contents 56 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
23 0 obj
<<
/Contents 57 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
24 0 obj
<<
/Contents 58 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
25 0 obj
<<
/Contents 59 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
26 0 obj
<<
/Contents 60 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
27 0 obj
<<
/Contents 61 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
28 0 obj
<<
/Contents 62 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
29 0 obj
<<
/Contents 63 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
30 0 obj
<<
/Contents 64 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
31 0 obj
<<
/Contents 65 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
32 0 obj
<<
/Contents 66 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
33 0 obj
<<
/Contents 67 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
34 0 obj
<<
/Contents 68 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
35 0 obj
<<
/Contents 69 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
36 0 obj
<<
/Contents 70 0 R /MediaBox [ 0 0 612 792 ] /Parent 39 0 R /Resources <<
/Font 1 0 R /ProcSet [ /PDF /Text /ImageB /ImageC /ImageI ]
>> /Rotate 0 /Trans <<

>> 
  /Type /Page
>>
endobj
37 0 obj
<<
/PageMode /UseNone /Pages 39 0 R /Type /Catalog
>>
endobj
38 0 obj
<<
/Author (Forensic Financial Statement Analysis) /CreationDate (D:20260813223159-04'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260813223159-04'00') /Producer (ReportLab PDF Library - \(opensource\)) 
  /Subject (\(unspecified\)) /Title (Forensic Analysis \204 Alphabet Inc.) /Trapped /False
>>
endobj
39 0 obj
<<
/Count 31 /Kids [ 4 0 R 5 0 R 8 0 R 9 0 R 10 0 R 11 0 R 12 0 R 13 0 R 14 0 R 15 0 R 
  16 0 R 17 0 R 18 0 R 19 0 R 20 0 R 21 0 R 22 0 R 23 0 R 24 0 R 25 0 R 
  26 0 R 27 0 R 28 0 R 29 0 R 30 0 R 31 0 R 32 0 R 33 0 R 34 0 R 35 0 R 
  36 0 R ] /Type /Pages
>>
endobj
40 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1962
>>
stream
Gau0EhfIL2&:WfGfV^gb".pi3rfNU4cm3_C->=.'LX+u"0abF#ChfI%o&&?IZ6:LG:8g2kJrsSl]AJ'DY9XGXs(M3m>QK5B_;A`0Pel]-.(;1[0&V-.qpD1h8;D`53"G@^5AMQVl]7XVWUCB//C%NFI'<ai"q'%XLXX^(,0mmMBLJUE/8>QNEe3&Q3V:@!DU,G_P>`;oY!uKjPL0P-B;=/Ujn[F87TZ@CDpui#*R)78lobdOmR<nST:75K[ka'Yha;`Baok3B.At[<?<AV_Kaa?D/@9,*Tu/J:[4;VTnTl).aT<e\B^I?r3p*(]go`5;<&eOm@kJQ3n@$c@##gU7]-PQuVYH`/r7VcUL7dFjTo7qZ%tb]?AWQp;9^('215jR@aCH><Mm@b%g!HU#US#hTaCa0Qg1F6kBa^QOO1imIIQ4aRgLOaEUjM4)-0P6UalhC'(T(&%/a!q3kT1?[KK=\sc5QfS_h8W2cHe\6DBK3PRHIG9FLcWQC6OQCjp[+Cl*WNEHo!KN=6gumEsNOIPiP9"[n"@(HTV4]>3BkZhpMp/#nWO*If$:%!oGoQ^h>Nb$HV9hc+:PP)KF[1Rh?+WHd#9,\]0D3-3`2G7?eTd`T$4G/ri78KjhPa$C)LK;7=?#_-HI7`*j30K.J+[)RDr2F,E2d"_hDgF_f`=)Q<&W'%?1eoInN_N;apqCXg1fj1LX3aq%?m)'m$bY)oPGF#_':]$[5YOu\Ja+F_P0>S0#WOrt&U9XL]Hk1$+HF!L9N>a.UiXCW0GNa*5IfRS9C`G"X6rs?$K*Ort)TiM^L6JU7c(I:nZRs35+1bro5So0Z`g8:A43\Gmefd!!j7=^Hc"@mudqbGU1D)uWQIR'$_)$dnCZk-kk,K*lbEuB0UFYqT3;dgY^k&Qil2u-:WV.\+JDQ9P(D*$QAa!0q5LhRaa52MCl).=mdS.Oj:6;C'UC10SZrH^AVKhU"6.H__s*fJ\/Wst#Ym#%qtkk0LQMgG]OCrTRg%pJ">=MstF)W]iN[W5'a'#al(#RhT>.,k1(lcV2F0I6p:T$"9NX_Jj%&CU5@k%1-$`)<t1_7GjsZV/Lk*tTY^([6QgWKM)7/Q;S,j']-*Gnb('cE5Qom@gk7F'eg7r5:J=IFJ>]JEIkr]Uos_n=rp@9)(kpC%EN;$/PrBDm9e_)hD^0JS:_r!GR"jBS@B+ELQ2)XmY*5$C8P8=8>SJ?@G7cP#])rZ%#L"bnMX5)o6JF[mSbZ?oiCH"Je]BAqD5<K`.Bg_1KZa!:V_!E=!gt\s0KKf,ghU^4^Kr5.jeR7a.MWBb`LC"N.QP<grn(2ZhI&Mc/SIq!-59&J2_=8b.kOdO&rbgC:6ie$MZo6LH`_?70P6i3YpoN1%M$Xl^q7(:FgBAe6P1,9V/bY`42.?+J\q8t3%Z/>FRaR',LflfaV>2??NVWWcA0#md`@+u+YsQ)ot,eKJWO(o69XoM'UO8C@IqkBkPGCr(K/Q<-fH3U-k\DEda?_[!j]6NjL5D&@C1_mF&2;>#4IlG<qZUY6^"C;Yt@NO,Vo0BtGbX#@UeD$P6F(i^&P*`7u!Uj.LgKRr63gnr4%O4hCQGE:*C5r];Cqi.(85.IfPqklIb(ABt$X!:HB0Kl==I%:4qk#)q.H3GCV]BK*=FW7#<N8bZW[;j0V(=bTqW-/t"#dZA6Tiad!F1HT#5"Kd,'boU>8)V%(Gg!*NN5Dj`B,%B[O@&qJ=Nti(0O)N0N\+1<<s1:`N>\^aaBf8-%FL_npDo&?eS!O\>AaB?lhZ.l%7`%K.<;"+T[&V[$b@d7:qSqXW/&Lj5j@2/@&^DHdsL`g/>L/s-VBMC'a7^8ko@[<%S&)>EKHqRH"%ZTA!=R@s$8QpLXiQmpY[4>MPZbJKr+.oWahO8qGHf^]`8iC5(G_?YJ;n25H<[V;T<g&^nE-KC'#>pFW/!96(NS_a2-b\]V5'aJHnYf~>endstream
endobj
41 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2052
>>
stream
Gatm=gMYb*&:O:S%'[Ou/K@cdW*=hl,4.9WGIrd12,G".$R=-/>)@8fWCHl9LXa;03`=rM8Si!,ndNiL6uiRCpd<8<Oor@g_ojP3KYi*CKK0J'+5lO6E]7t^c_iK"-Xre8a7p\%OSSD1h8Jhl4-AGW#^m%?pjQaW)18$_'8G-EB8kU0*(Jr'NPJuiAA3s'!p*#b+K\OR_?f9a9J<`sRbru0hTNig)]FApgl$[?l77"Vh[$BB;Fm'"E%-'UY>Y$5k20SG63A.n=Jm/)Fk_Q>>_D[GOGPA3W.\gC'gDHrIYdP9P"%&>1IO^+/?57W%r$MkO#b]Wp"HB0ns'3dfCp2/m5bJ)KS6!11tRBn5<rDNVO2noL"'c*&Nqa#4mgEC$7+-f;PNEH?Ik%AJl6EBZ@]\lW%'Bp3e0?p%UumNI[",Cn/>[9On"V>QZu%>g0h/fD%)U9/g5E%9-hdgZ=8_4+R0,%O`*!PiQtOj7#$s9A$,+&eF/\ggc0?%:Pkdh+cML:G\@8fF*6@kiH(RQ]Y#><pET(K%2<gt7L0_686:?!]pU-hpB0dGUFI(W<=2jBR(-b*7N3"TY(<L!S97['+DP9ood3j^i]0J:4[\"Xeq<:Cl.])[gV:YXU6[>)nDWC9\p/OuJ89?X8l-rt1QXSVB94TCUG6M/=7[tKVV!LZWAGqR,ZJR,7G]eb>UCoG5ZPH0\WBg0]d]<%TG<1e50%'1as*;ucjE,EY/G0[,MBkEJ5ZV-fV[1;isKgsW74a`"og3/;?B]g,]F"I_#$`T.P_#rR8ta@CU9*D)^iI)@*9:rRo0GSPq.F.$8jWuX-\t=&qa*;eS0/UTgVfEfar)@;lQ9#Npo",I="@?D!di6%kp_KEhkF#,BOGAmXD(rn^6"T;pNH&B0;Ib4"'ulOJXc/i0oup5q^Pb$nE'3n9ju)IfNW?A&c'qCh7F=1#,>S[OGl_jI9m<WdQPc2?&jH^<64cL#.N4\Nk3HA!6UYLodAM%Cn(uVuIK[b0pY*)*m'nM>=n\M7h7hHn-oD6%F7LP\]rLZ.MN$]?IS$V10+HO%O(B%[qd"]J\BdM=@cCZ"(^7U;J.KT'nN=R--O3cnL+qEh5<!hpQ.ro&=^[;>6SX/iatAHGZ1kO1;&OM<Gg*,k0(s`Rm2G0V+gj$N9&MUS=BN@Z\7\-Z9jgc8mo"NRnhN]4fiQS<Z,!60A)^.,aGW>dq!:+;/2&Z*g1L3fQ;8-D1CIZ%X0.bmMCUFb/9doBpO@5(AS)BE^?7Ud)d>o5)(C#Pk\-nR[]`ZBi:L:H1t>(#UeJ.C0$6%2*=XiY"$[P)#Z7hOiNfNm_W1%H<E;l.XcTZ9^[V5j\8N'tE;i%cu_->!X7*O[Oa('RtB)AclL,Y&Ve!_<>4nZK)jjG'"QI;dU:;1.j5kVA4p)(dC-V6?=n^E&2o`q6.AT50BuBQ(ek*=_%OY*2M-m`#!F/mJ`rt.$7OE(j/^pgG%5%P?&h*.RXs<m8]kBYW9NP`(&Yik0[$uX_9K\C+$s>ojg2+W"fT%6gk13@F9)LKR?\q&>T+r4$&>2B7/QMi#$!\9Ig[0.9,At2-6cg.$b\:c!Gt9\cZbna]BeGX@EqS'u`Y427.B6)E\:.JTuZ`#(!/j[4JLr6hg]uQrILHfbK^f(p.tI4Q<iaNAC\T4<RdX399ae;MkN!26Vp;-!?q[@Z4,6MN#4;Bk6=[QjfUST"#?K:/WPb_ik]'asHhU>uJG,e-rcHiUS<o+MGrEjpV+jDFLrJU8_*;Fc"Ph\2AU)O0ki#1e"]Gk0:BIkF]KN9%Q,r5d"m9C/^'tY?9b'`*-2:I"R2/.nA@mas36fX1,X>WN!Q41aE"JSc*X;2ho"#Q(jdua.l/\>'!bN8;^SO,?D%B]m?pX2dZ(^g7"):m;C')\tuGc%diOIqG+YNL97WPU[P9g.COOOmE.Z)eOs2r8[6f;p!%M%eZE-rGb#OQ]p,csMQL2W]0_d#ohma4UtFt.;7F=hlt&JlY[Fpmeh)gI<^f%eM'&[NSZ$N?s(PK%e&@F7^*KgdXnBp`;o@[GKopiU~>endstream
endobj
42 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1989
>>
stream
Gb"/&?$"IS'RfGR\AQ3^R)E,+Lm-ZJfdVV1YT5,K4$1[Y7<K;7i(-/>l/pmlOW<+I)m[9QJXor:$+6W,Ffs$#@MIfTo:PiAkin>'S2"Ib:$9HX+JJ$[4eEdD3XWlH)GLhO`^prC'7>k8/4o*^Mk_DkRj1@96<P5SP1"I=s&[Y1dDfRK26]'nQjXNb)22Q-P)Z_'_uiK+E#[FV-uX&udj6$,PcFu&()=M^GsGHY-mKK;J#BXI;&H.SK/7@tZ8/<k`QPZSp(:"`d.FSakbCf)i0#_$/QZrU4e6>Q$_tf*]G*TjeZ\UJQo4!MF"nWL1EJ#Op!:'/D&\Iu+Gpcf`q0Ef"N=S\hkI:@i_`5a)Zp4ECDO0sKX+"K`/K:-Mpc-VX#qQEY,Y,/3'p;5KpbHtQj*-F6BecU/HkTi-7`q^gMqYbq'b&YhsldRN=4lSSU2n8NMh;\PAuD5?p;#L-&cC[`7UjXd'g)_,gVIU(&^PhFfc!35JNklj%HQ=Q*t-eVnA78D3X)`\i;iuo9<QF"&N'[#'@25q19C;Oqm,cQk=8b3n;Cg=6kV^d)W7I.fg'`a^d_Cc1#KLOQ]kL$bp[6'j%s,-/"/W@OY:<f=a:0HUgQ,[&GV$n7G.&inDm%pa6/1X,V_e1cit(:Fe_WmN"ET"kp4><0[4tDKqa_FX<1E>ahM^hQZ*2c:#3tbCZ3dP8N*,'u)@uOrK7&Klt.%]>/2hQd-n#8R!'=8Z`n`C*ls_+"hhu9ne(0K7gZi#!?fKNu!f00(<icHk]@#2T#1oIkl*nF8b?chjg:Xj--gFh/c7gPXVMP8&1H1L#RNK>Z"<.>It6ml;R)=5pBgPP00VOiZ<d!=0r3"<<rZpEBl%L9@>f:>MC'PSM+AI.jLA8Hu*P(/Tb8TDPCsW(>M_4<,I:m>&%jcC9rN(VSPJe2HApeak$O<@Y&\BJUNf9Pp9=.k>cBWIg7C?B[I"nNaIMjasN@5-S8B8(l'`&.%#sWQoS=k7r]G/MGS2=jsY)&018!RHk^lW%=`VS%m=&`*PHY;6#k(6%4)5c:3l39#a@.eh;t;qJ]?OjoCOi4-ZH=<QWNtXn3u*FQM:lS/dHbcY#aDQIhM03#l>A9h=d_TGM>:*U99/V,skmlCa[,RCqXSqkYnT6&)YpBFbH#>a_2T[(L0#8B_o0Ul@Yuh*JI44\"A!k^*doVS2d0g2sRV-@gCO-)(0c5U=Y0/Lp3Tc=C?IHNFHm/(*!prd]%Xoi0[nF?ejnnV/45!5;?812U=cDQIfMqQjqb;6Po)D=?Z3HkpD7<hrug`A_+4D_E,,oF(rG='$%[:BaNOki=W[73IK`g!eG_NA[QE#qiBYjTGJt'(BL'l[oOIR>]_O%0<lHd';a5rrcmM^&bA#1aNm0ZlVmV*G2#a)F,glLP4aqeh.LgSpdaL;+=GN7jWcn?Yt9=eDRb2hGj;fR'*A_Bb=fYjg"WZ@Ro#f@s)9cd;9;g86[8k]QKT<IL?.hP$stUQJ@+"X<*)-ug/AUUL2QZsp.s\!$)As]V3.%eh#uX_'5&%l*O;NMrRg+[`-TLU'Q*u>QbKN5Sba6FM:\t/@SA1ub)lV6jHt&?,lUt]lh"m<D%<V`blRIj.1_I;5rhL:_uF3:0>o-UI/1ZP8Nb;l#YCPkqi['Yb_Cj;3;CE3^@08c'U>&j_ibY08Xq'`/h+!u1Rb(up431Kk;mWcGPo8.h*W88!ChbbG9N2c=&SaL`1Uc6n"t'hWV`.=?6`5&>e]IU"J"LW#7paZ]lg=EmT^E6+6:Z;$cln6b6On[=UMJ:WsE?<.L.K"YE[D@jrUd'Hj9Qo%.sGU]@.4XM7EbcWI0,u;kn04KWsh:h=D\j+H:44R^BlUNF$'XGJjB`RIt4[[C')WXfUrtQD\9-U&;&'No>aVZ`j+=_;MbZG[p_J?n5<.*rq)"Z5das?6Y2gS&3X)0S`4`9)fPM&+`"8bG3\WJ`YoZ/0B@#bCdJIQD^Lm!BsS&&H~>endstream
endobj
43 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2314
>>
stream
Gb"/'gN)%<&q/A5oReZ&;A>)+Pt]`ZQE41mRoLX[elKpnIMi2SE\(I/$m8#h^Sb]E&@uje[ZdWQ63)Y+m[h._dmHDbIYIaE8toD=o^Y>1#j?S/,4Zqh^80B4-Qc-s72Q9QLqH0@qXG3M,Y4\tIf%`R(XrAZU,\l(%]H0_?J)lAhOa?@;p9g2AM;>e`%pj!j@-bdfZ/N8B#>!EDj2!HT^.bQB>na==/r*H=.)SIK-Vc%TDjTuh?A?>]7GmO;3fNHSQ2u*1YR4Hf,s5QHWFg^M[&49dC+n3d'oIhlRGh-74+4Pq>mf!6+<l)UWe^uHk+C<XQoL52UO>r)Fe$E_Rs4I)nAf[:$2E^^CHG@T2MpZ&D5SY&9.c\"RKS`?C1q:[!^dQT0i6d#mU^>aa%"@Ls7-)c5K.=<oJ*ulY83mC]8V*J-RDHEGr]W4]18S$*3RD7WdneH,<o@I&)J#(4%/;,#)Goc$lW(QQW-V:tj>VoWIUi`oZ;$d`-AY-Ws;JII(L<f,B_C:05$0#_0(*#VF7YFeNm0@`hkUZHBO*aKud4<Ri"D@8XqFB$Z:_<K#[C,m:YN>u6Nb:'<Ii=#V]m8fF_]oV9Q.\\aS-b_[p>dpBLf`817\[.ia^G:+??C#j/)F[PGT>p1`Of#SidCcW%hUrqt_DKM.jFH%k]@u@Q][i3@XZHIA`V/0Qg>XXpd0naXZUD/YdL>L5`[Ge+8Qu]N&D7[SuEbc-Gb!>5!%aYsh;R["tnc$/2c.PF5lnfF4Z'd<((8C91UH'J#@f7u2:^!K%T+p7O'LB5;7"T3+T+q)O3.l'Ko_%<&^:]8V2)Fq3OqepkM_j$(7;J:C]6V\1iO#gq_K[<5_$2!9KCZTX[5KCWG#jqkp:6+LThoAT6l:.LX`RFm"BeY,FO:g=W&_O&8`Z_s\+NKRd\]M]c'HpL]q8L\01:nHMs4340R(t[I!lABl-jb(?HVD"[;puj)jPQ9!QmMHKHOPu]N>Y@n.mE059OmTLdJq>]ElA6A9b%tI`cVQM@84Mrr0jF;B0j^E;(q\"=(:7Z)2KU*s]hmK\?nRLB'i&j>$WBkd.K+KnUS(IgI,kD!!,CIs>#hJOo,C9&9]R%+LQmBLhuI"9)_`I5bI(lf1[!dpVh,-S`uX7<*7(.@G'4^r=?s"r8BUmq7B5/7lP7n09ki1\Pf8Y'#<K7ggnDHtV<REJqS=M&Bc`Ic&;6l\s(D))@\fG-%g@r"-j3'3N'"of3HNQl2t/nD(hRhjXEFY`_9#$taFCigP0+WZt`8Q9BO6(^k71E5mT$D7O#`<Fa^O[a&d!Fccbo^U;#gQt-e=btiV?d7MGr4*[sb2G2AfP!EDTjV+kDJkL8U#P1gk9H.j;HC"3B49\K6rM+8=m/6/9(#Fe/er;62^2@gNH<#UBS2<#LkM?TSC,uYJM6*dhme1uu%RYRIC"S_q=mH>_Am*sN*0sI$AP/Fu/_h_Cg^Hr(e#`taB]hN2T4)SL)31l(:STl'(7&A4\F.+sc%WWC!_UX*!lWe@nD],_8$+r/*s#9b@+=[Q_I\.0%<^5`K%=4)S@Vd?cHiY";;R;f%j*shiB56jp@5Dba"7BX3b=!t[DOF]Hb\+P>F;;eOBGfC@/uB3&R61).juO?O:D%%"BZC4J$oHs*QkSRMJ3I8=`g1K_Su(apA-!,6J?hkmY[$E=7k2$'dinnbS<UpfA`oCHD4j3Gd;8M(A[mpB5H]YN<O=u-]seA;6de>ahV]<G51cIoMgmtj64uQ4tW*I5d>pZ9NE`nkjf0m!Zb%FW'1bm",1S$:,%We*40!MY9_iMJ]!^dF_PVnQAi@bS*8"c9+&*0m;#`n>ll,U\Mmn\geEeF\me*Ej0Y.aITBKSrnQ2EUXs\cll1.o7f[Y>Uk]lK8?TmfBk&:s[/[N/DICu][X/"r>al.+l&[+"\lD24j*.Y'7fs:A/tj#S1R2I5@HK3S'Y(_O[p&1pDV&QF9uf9_`7C2:@uP/LmoYD6XH/+D,>(&#l6"fTNLA'?I^5A&V\2-$0=#CSY.Q^HR9m(#'][[E3H5gu3;.qc>KXYWUX^i[O7Q^@FjC"R)E\s2JFgqsMp(]R6BO&'@$=juL\!@W:s&7KQH?#7j5Cdup6+Y@$gc?LVq>L)n4/d%r0>-D4J([e37[+AX_#KbJ%YX"5/'5$V:BG3)>57p"3E\J&!&k&+21*EeZQ"leUBP`5MO0Ejh58<r/uV([Ge*3-#[2kU#$:kF.@5=g3;h4gSKO,0-+Kq.rfD-&e%%fOh:I^`j1O&6aDcKrWVpDL9J>*LgK+OoGW3;]o"4XoL^M2"'.].#l~>endstream
endobj
44 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2286
>>
stream
Gb!;dD3*F0')oV[@^$r#:15Z![B(kgLNK";Ea>JTCZ#b3^X+`QZ^!t7P]jD5rgk8Z=n]S&\Fb;V(0Po3Eb7<&bk$pV.)\pBI[>DUn!E\C3he%"jbBKd883?:DjM94/qQNT`C3D8,0e$,^iLR[Bh#l:GS+J.Io0.1;P(k7V^u&^:DNhOd2C._#8W6C>`_Fo4Bt^EG/gg!!tgqQ08R34SA>@\pG@.o*Hkm<)gYSP!StceS>'ur'4$*H_`75if@n="Wfl5gU3a&d^7s`X[/?41]'.R+\9*ODj=1J,V^l&>daVf#;9?T5eN`7mRKk>@\6Mhg)2#>7Naj;0A"uU6`!O<H9RdUX8_IeF0?@onGofj)/PlSqFVI@!*,16i`=W8F*bT2,QCa0NcKZGWNY.K$E9&K,aTMCK1m4:Jrtb80)/1&;aM"Yoqp1HCcD$[ROcSM?<??EmOn3kYMHY7k5nk)m&BKZ4O?o+#;*ILS1jQ9%RQ.4SVR?q^6Q^GTDuXG6>-:OLOO\GF-m0k[K/O2'RNn\hW^U2C;:.+1P+N9;K9[5,TsjsMMFq`M>a%@M>%+77gi%'#K.Q,5,n2/_F-:"gRN,R5U4RebFsgj2h)N#`G",)MOM\e;]nYcm)qgJD<O5'_3?/kJNA_<"bC_KXCW'X?-+O7gJ\dc2bk@cFUm[B(f]NGB@Gd&.0+5NJ[5"t'gibTg;/(tIhmr6XXsB9%2%%\UdB6J:hXhA0Z?2kD-%NL&obNRPZiU2`:`B&d_JaV?:7]X-"5J!+?oh)i;#m+%I-):W1XYk0Pri.JZ-o8T%d'/GQ%n,'G&Oo]Gk$.:8:Y?TCftI)S?Amt\.oHY?:iTO"XeX^!]@d6K2K_*6/o/XZkIYH<`7Kg6RAi,`CAS.FW52kK57rmZ:3R$T3k>%(&TM*,L]9u-NbTOAN(aA;)gC#1p0F>;Q"'Ei_cV()l!8C<Ka%UihVC*3M(<ibL+rS\$kUfNd/4Wf@O`OAjT-)9!#+HNC1Z6C^*R-Odc5@JWG2HT4ek?!P)C)o\#>L;87)S<=O&Dnso<kk_^?bNpZ)c(.ap(lC,&9.\f!rd9;o]JG+)bC54jiN-IOcEF)HGmdMd;!1ect"iVZ[,$(:(S7Dr4@*Q$!B'gHW@(=Ij(SS1o.FMp4kkHhQ'Ps]f,sBM!eHo.C=2K%eem6KAdqhgc$YM27$k)[1iT#csr!WOSJ(FBl0ARE;]Ep]'O)!k*NJ&Y]iGjU!2dZ."'=`^iq@3EQR2n1&SSTu-gE*rsd\g.ChRT30gK.=r=VO$)`"mb0G5$Ne0`0t/8TPC0I'a]\0:0CA5X/qtOQ5S9K`TG8%ZJO41HR;dU'@K/qNkpS8&XCTn8[4-`_GeDmA6b"]NO-:h0]-".'Je9>d&iadtat_5C\0g\UJJ'0F6,YStj*q-h>39\ZUsO:XkeMDE\UMob*eJXstEh6s298oCS"tH\A\90eki9E%F0UNZJXi)4t)D**`0"KH(#JPN1<*E8dnZ.-=9m^hX1r&(<Y1^!cc[kjB'_[Kc:"p@cZ)nD6iCZ+)fZESR:9dEC*!HI&JsQAN$_SXc:)1@\L2VQ:<^=5u[ZXQ7S_'&n&;%A+$HL,0tWSLtimm>3j,J@.R5o@TE->fm/PL()\FSiJNt=_[:<hC<;FC#+%8g52!7Nfm\*\oJ(sd7AF6YA:_?]E=UAaS'!ZcG,RdpUZZW\$'+SbbSY&H:#s)RX_`6SKn<XW,9^*&90\>Z^9r&b%4!\S/8dH;29Pp)&[YK4[O#Yi*e@+1=mRj33mf[Qoe'XognDSfG[LLi!(;0o7pFJ>fj#!l#s\6\'Fd0)uo\h^uBa]k=*8@MO.L(C;*8='Eq\CJf<)>,6f:DLcn:,i#(YF'NP7eU-!:%Is2HIe9s!#2._!e#kq65pCW'3b@cuNI2Te;!A2#hrCjN9OMWYJd.AUf:&eu4:"$Q_msI5(LTnNq713?C=W8?lf=ddP98C+l]VqHB4ppBhANYqt:&@`k:$ig2Z@)L@3*cAd4<=0kUNE?`K%p5$RV/%h?apm2_hi>e@?G_:EP*.*"I`TarFm5&MB.32E$pE<-7&4A>:g">GZ3l(PC)Z&2p7bljS0)JKrT'=H?XN1lhR+o*RLG8AG2R,e=K1$DR^[Who#c\ERo,an#p627r2s:]I\]KmW[R'C_VA)ik^6F1#="+i'[33r?m^K-dP?3s5o2]"?3C/Y]G!tG,MOO]ANB_T^nqbEh&).(Ara&R<4]GGBEaLC=";?Hn70/F$#ies+B(@ilb1uI+@:!/I$6nMuNd"$O[p~>endstream
endobj
45 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2172
>>
stream
Gb!;cmr'/U&cM.4@NZ@dk9-mnqbq6,'YZCfjD%q@NJ\p1^JMP,`7utH+h;dghtN8gPpP2T"bBl_*Coa"gu7bIb^1=!1&`p-=g^X^/Eu/O&PHfJ-C.(</[+E`o'Fh.1f*^RO\ms]auEa9/<Vd3l(:237601p.EXFro7U;io==n%U%`2P_%LNkEA<i=1:AUj3CVV//<;O%88m8kCiIN9SC=d?o?1aTjXXd(Xf<SV8W&[54Sq3GI7W?C%hi$8(<X^U/er<u7[dDcr(,$"h1jduCih9kpia#E)Z-(3GH)9ZOf<RMre.KS6FT;MW=&6kSml>+Wm9JI*URrb1sMa?KmSI:GC1X63*Q1eE#f`20pQR8+?6H*_X[c4,S"9Q;-G;l[WhdJ9W:Ce"i(Fl$4&F0Z#`%UV&!UN!hW`b8[L_oTZk"?XQA"?9c\]=!nqY=2k'3Dk-$/h4n,Yr#QIPhaKj_-oA3aLE%cf!&W7Is(cfLHq[q!g.gm>Lc@>8Rn7YF`:9)QT^iatlU%l99\Djqa,jr>l^=rsss%FrEU,Us'oC'QcJ[F'Pg0tX*kgcT&2f^M=@s-'s9uc1Vl^FWDFf3uMQ<QYGCA&pTBZ\&\7b#r\Q6]-5'3&[[,r1-u?V=%eqig?k(d\R4//,%H_Fu=rUu?3CCj4OEC:J*)PT#!`HKi(q2d1%o-6,p`>@FVgi5JG/WeJ9T/)_NI\[)><T@2Or<fbQiY(]RPPFm0#h<'o9bF:u"%3A8!kZ8ipA`^$"VZH!'qg-]uAY[ARq7mj,r%K?l*@X'EM"Hc?8\.GpJ[*!dM8X!Y[=(LQKbsP*0<VVNST>kc^,!J;TijUFai>jXFD>;r/Z;.WNrr26:+D=%O(?cHY$>A8XqfD!7$)G!TGn$`jl6p!rR6l>(:C)emBLh(OKq+dgXaeP0[h6UO^`4kY2-XOXLQjYj(S@Aj\\;ofedZs*L0]kmU;h%)n4jAMQEWe-Mh2%P&`kaHne)=R\L#GKVHFJ9:=i1H'7<hitUV+Q];/\(n@)QT>fYZ+<7QjZ"KEaTEg67TQDH]^u8.FRSOrLJ]$WhA'u8EC[Nc0cW:Lc^_T_9jX:!+pdNs3io<h]\hd`9jKAE8IO77HM!nF?muCcOj`-IHATE=jX&SD(6?[Cd*-J]2K]M^a;r:_bff/*Vk1,]:V_K>dq1_ORXO"_jCp<cZ+a38gEH(C*]VjkX;A0hn>N9!-(ugS\"gS.PpKh0fj;a\sdfNNaT,!K)Sio@Xh^Tim^iD@n=&=EW`cphOcH1dNTJtRJqAk"JH@UKnrGHZF\Y^m^dQL)`AQ-HWU&_;ffQ)aa]#mO"hLd8+lHBi7]QU+!BdNS>7`mt^Ec=2l's[o6!#-[@&?fk:PCEtoEq$.BqUWVH@/;qR!AGPi(ZY\$@uJ;MRQ1.*D#;T4J32C2c10s<(=nM+SCPB29!g*2Us-$eBnm\o5YMN/(f2,!e2eD`EFgYhrF)=Ql]%9_IRGEfK5$'FKWTdoD^?^8ltKm9jhi4UJ2A5Y&Z:e8+6"H'l+$oD"6:*3Z#1e&8CsWso1D*lp'LAF.%Z6I<'V9Z9P;9.Xr4Q`P[ah`I--^5(#j,S@39(.!I?kdcVOn6F$Vn)Me'8%hpcPRH_/KgjSsnX@K-!nk8AUa3_uBCoCSO:4H#i/o5stpFIkUjF&6P%$)&?0&,-f95Ki)$nmC?qkL<TMY5H"j1i_\rq60e;NKlkl(i%>j,c0>R?c9b`Xt'DC=/l1<ZWlf=lNZ18K6-eN3DecGhZ9OB<tS_^DQA:o"f]jR)MFTh#WTkQEBgd6/bl#J4ERI,3/Z0?#2Lm"^b..pAuJo"^sVS]4,(FT^Nk4Ia5mq;CVVBH]p?7KS^o_Jmp9B#j+eL)M2pAu6OSi1#u(DkCe$!q["FoE7eI[*MS1N-#[m2`!j/&jaj@sgil;PJE4#Q/,U=f\pR3bm=^4j&bZm+<8JHJ.jMY*eL5sUF^4O#5oqR<I"f\%P3dJcMot$(FMd'>F]o"3;<?p5H#"&mIC=.)#/'!782$gctnK%So^"4qT^%4BL=raT5!Y88jZ1d/M!(-muf(Hr*I^m1lqdpKVNV5mO61Wo"g6'nKI]XJ3&pha1Y3T@UY<tlfK\1g&(4gk-nj#MpUd#$9+b@F?@>qrrH02jb4HHTC%jVCJq>9P$*9VXYTsOb!ZGh;t~>endstream
endobj
46 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1679
>>
stream
GasaogMYb8&:N/3%#c</!gtAa;A<=LKbMBn>.7%#]`diJMHia=P.UASdXqJ4B9j/^kD%]P.-tLtB?loR68AJ'n6NFiDcUt&P>IFjC-tQ.A[K%FGH8j',[/Lb[*0q%Ajr5VGV7DgbN[LEP:3@-6rT[SOf-],ShJ!bLAmS\%2Lo*Mri>kPU5E8?;d".NTDl1'!b`UO;rl[#+)]3BmSTW40b*ChWlYc]6$nH&mtW02kSPYc%gulA#4@KU2)?LK2_1QXmTorRN7.HZ;Y_q(u(IZGoSr[27erOPH.(rJ&^'CoI0*XWaT2a1O-p62Z@FXbgX,MGo!5tKQf9O6#7h^B4jF1f@/\I9LYJF#`Nnh-M[_IU^V60dC`$AXS`,@HigB$&5Ehe!-&WD2GN<GYbFTJ7t)hI5<5^V7)3\0qjm4%XMgF#>&?1GL)g?6HRX)>YBl+,SC9?<<^&"^41aiqj\I=!5KV2Qmim'&S?0j%79I"HF[eGaDJ/gCVY@;fHXj1@ol&1IrrRba=<NNP_=L'_O=_WTS?l]pPs`,[&sl8L#07XT.*7XJ=9'e=^+k(,#:ZaL8m%=^f+5Q.e4+GVS^Ij"d`.`AhHB5.]qiuOf3>i"rBPR*_3l37:&u5)b-J[,2.S+LUU8C5&e-iS]PIV4A"6"rE:3\ZRnl:Q+UGnR[LF@eat"$]JoPOZpX4Z,BgK34PlgbD:8/L2`<bd%P8)R8Qf.U/G8jp;jf!q.RVq3?p&Z+DZS;M$>VL4>MKZF(C`oGeN#CFkaRs>E!3_G+Je]5J:DF/A70(OC_(;c5/GOL;r>4#4+cFVJ4Fe+Ib'k8*2O1jlV%mFnCeblE6cZPA=BDBeUfZN.hc\EHGLRd2"4\UMqq`B+S/RQ,6j9d[!s?&#`iug)[d>#R]FD#XZQG`r\or0m1%i=d@r%IF\9g(@'L'F<ZNc/2d$-S"`R]oaa"F"J&^#8?=p$TH,M8Di5W,PKk?Odj3tLsc?DD^>XH=Qc!P)i&!=5q0?VZgFQZY]G)_]bO149u,:L=Tmc[8N*FXX:KUuhT/HDg\.!)iFj"@dKBo`$,[U4h*tC"T=QZeXOK;cZ*Sb+mN#Op:D2E0Xa?H*eF7,=ZPBALm,^P!bGj\7NKuiIG-,5^jrB*M#EPVO,dgcfnIob(e?F3Qg%Jr^^Sl+R-N?,:$rrd0j)8UqDo9L)T/U6LIDhiK?!jD@OO(=cME#"AD3nZlB/J%fctNSimPZg@#H=:a7O4lq\P4n*;QPB(>:L>_`k]2GW[;B,UZP5L&5l\eCsW4F,eSk$rU-k@L)5n6FnT5U0(7Q&#'T*&N;_X./HtB,\]K8:6M,eOWFA,s,%@_u4B_C)sl*EUr)?N7PZQ\;@WR^<X\4qX?rN)50-L'^C5n63[1&R!JeF)>h+6e^84^Fo<>hE7>g/7^5]2gPQq%1k\-\A!$*A(6X3h0Ltp=>/lRA"ck-lRX,C3`<uM0pZmtX-09B>#_g+!/;IXO($!Zj@92r\^Vg51DI-,uE-mtNiKYc#dk`"OGfI&<r&BrX0rgZ$V.Fnk?d7X,Bc&LUXX$U"-!e@^2kp<STDNP/I<qXq;7@N(T)?U&K<)3h5?ir9:5$=P9-:q2EE4F,SGq,ufU,h4/2KCnhf6WGJe("J)Ai0dlF?"d(DIeAWSgP4r,Hm<3;u:5AZ.#oq`(:kIlir7X8~>endstream
endobj
47 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2496
>>
stream
Gatm>D/\Gm')nJ00gN4%>Js^-U>G<W3$dmf\(C?#m05NafIsU"gY,2_Q_`4*rV@!Qb>,@JA8d=\`:T/NbWHk/RNY$@`.,`(/fK8pH['s/J5Ea_!au+^qk)hSpK&H?Jh2dnc6121)TFdd-8]9gr:]/N&B"366HgR3.5VUVR;:@BmV4spMIUVFHp:oP8=kJP"Dg;**27t6>1j/%hC(<k#58SNDX,K808+m8Z3]AO9i<+mr$T#OSVAuh"a@'];HF%W87(b,V8%`]%rhQ><TpMoK5p6cgET]qkVR_Fb!IK_]&:!k)g;/^4peWLU6gf/)E"9d[cSubV!7EF&IW9*k3])GQ*1=$O2en&>_g-e#Upq,#Uk$V7gR=&98Q+*oc44!=s*o68XpoBe1LfR+A-@lEWcqc^\m"hbeE=+DW#@Z[&I6.T;[494NYKIq0?`h6=fJhCR_k:E<a]ZN54C5PjiZhg+Q2G\ATdd?R'ej:q'XK!(T?&2OdkeI'f%r>rZ_=RTjR"9B3hn''<?</5-hEJ1s=<jHL$oM"fQtn?-OFY'+=?j-8pG+]N01MXgnt9(6n(#7NUt;&kI*bjeU<=FPH/\iG'ugdV[B@X?[=K+dOl0(O]N]>aU]ansm`U;2%2%g2\7#3,RsB"s0u6?WE0Ws-*424,.cZ&f1C/T=jE`*HD8>R^]Gm<_Dm"+#;'Mp;;-Z`[76m1KP'ZB?^I/(JO^)@DMN/61H?/'7p6Mdlr&6`7NXC*i-cFA`EO=9$=KQE?Z%g(2'i74gcPlmf>o'sFDCi-W0MJ"T)4iBq22iJ>o"P`pXR_R;e-%7V:Q:hcd'cp9uhXp;YHALC-8Dn%P^a'o:WU,7\-BfPS4mUDlnJ_)LM;3_32AU/2TCcYRt3J)od1mMd.1tj,FMSqg?L@Cp6*DTt"'sEZZ.k/jAT.>#\[-f?i=GK-\KmN`9Gs`N'c+N6SE`Rb:<P#,5h4ZK+Y+\h^Ag>IVKc'^urd6\XNEu$20)Vq^kt\flks\AoiGhEGq;f)q0?$/$@Je"uo0=HrNa$kT'ebMB#e5cr)g<ikkD'PG.pN`u%[ssg^kEjUa<_P10r!?g;%e_*8,RM@\?#F?Ke\+Y?J=3hW\KHbbB1$'H[>DCp->l@l4F&U02]7JHOAm>=p5:b<!s$'lq?;Z0TDpNKr2Nla%]h]\UR9rM2hq`=Yu"<:ST2mdjR3b$.;=2=bI_-,.&W;K!WMH4Lo9URQ_f8A2kp3pf,6W@^fo<UH!Sj']pDPBo2E(`maF_nKI]001\PcdR',\ZLNn@a%,)kisE>2rqs+L35b"QZM95?$]jgsr@BSH:(hBEk?gWfoEjW.27?<ZW#0R%PF<=5JM2N0=oLMM'B\=]EnsUB]VtV_)EF<t<1(&nRmURq:joXQ78,o7Ku7J!nJX;P/R-c`2t>3CJA'THZh=uYBgt35Tk!lo;=SRP1Lc7)i*CHYk&#E0'47CobWP&?i]XcQ.;8[IPYFE4:`h^K.(!;[\Bm+#h3Qc,+e>a"%7[S$KQ\MU;r18ZdQWMg(ON#GQ:2jZYYeZ=W,T7IIE:-*REHTt_,Oq@4-U\R<`bT&-\:r":d+n2ohcFAUVM1QiIELaN(tWr^(Rm2"3l&*(G44O"lE8`\Q0$m@UU\W,e@<`R\GEgp7NZK7G!G)bI#U3'n:%7qbG&':9Lf/RqdF4@EWKR(/gb*ZkiflJ0nFYK7l]%+tkF;U^X9O&)*VB/3@@f(A`ZP.6p&l3WZ0Bo)%aR2@?B!'fS:Aap-tQSQGc7F7\^mm&L`R*o'H/W?61.ka&HsLQYM:]r5mig1%5(mAgS&6l)_:iJ>:(n%)])C]#p9$%a7OV?h]AJIe=i;hDd*Kru!\P*014,l9s$B%^[f@jG,R>A,VM+uu`eS,5!DHSSa8gd,;Zlp;Q`mFnFV9!#UmpLj@#=C9>JEbWjjjD%5\Vj>L>OqRt^Ip")nCpc`j4>/11_Uc;62EeMB`*1]V!3AMq>a=olD'(=Ag2Q'fFcpLP(cHq`k,!eR/b6QQE;2VQ*QIq'U%cV&(s^hXon_-pN`\<Y5Ku)mN1.O?nPMl@d43J#MNc"M.2J:5=/P$@'I$k"R<UGA+%7Fm/b$EOGa`Lm:!79S'c`X3(Id(M8$jALEci-0GVNp4FS8R#P48l4HJr>gbsV1@j87M)gAnQ=&o)d-A$Fa=(c:5"A7;\A[Z>LlZGQ@(E]pW<Ah/Q$j4iD?)-<8CYYM1O:;c\8G('4IARDP6!,H%0I+4]tZmPF=!LEoge)NJk;K`H?IV(<Ppk&Qj,O3W?>l;-,?qKOkQn40QIsVWC?u,MYY3i*0Ka75BahJIU^7e9p2mi:UWkW;V/UQ(fd,F]LhFdHh[Pcjkg:O8r'O(fVS./A4*McOr8?m<!dc#N([LU`I$rUmN;L@0I95Wu;9qjq2Xb2kC6&MdsPT6L[.*W"+oCsG$#C"Xl\+/BmI.T97>`Fc8P/1"YT=F-7i=;?1WL""=_dD"TB&HR*KmK<l_ptBW)OkC~>endstream
endobj
48 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2842
>>
stream
Gb!#\CQmM](&bk]i_Ds<j](4PI#(Z^S^,foh//=3'5OJoRJd2LO9D$sAUrS/k1B?4n0(D)A2heh[:bh!&d0iTj.(06aN&ehI]#9%Ik9j\Pop[cE_RbK,$Ot20:,`^Y.T#s#E+DNH'J*o!nUS:6o"Z2qT=`\iMrP1U*L4^7r^Y8J*$=rWgti[(sKL'Vt2+;R/(goU3<ip`reV>_]O]c-o^+TQ9-#BjSQ&aWJYSOe>'W`QB:U6hp\Y+#(@+B%pkMj'iq5S;onmaCAXNemqDM;0BfKq3ocsk[_Yk8moFa3(9'%mfi7,!06m.K\l\$VdcS*_-<M,rMm>B+)ltld1lT'iKR)t7DraC8@PILgppD&'o-k8m"G(tQ!YNc:Q@N6la:"1SNYX#1nL8"Pmbm"'2DlNk/n/>Ld=8U1,&%`k>=CWQ$d+FJ<\0MO>3eKjWKoR3Q!'GcLHG2',L]DHRgG+K1[iD>\MHN2;gr\j?8Rsm_I(N8,`H]NHQj(HR:-U_IU/8/>`m6<:8P'F2R'<r=#<6uGmUTpT'N[i6TMf/Z8@I:^mk'OYSj5(<Db9XlXkLEUe/&f/X=tm+dnZ#:DcK+h!Jn4IXh*>64^Z];Z#^:]W<pPVmWmsZ5%4Mq7r1n1lCH$M^DEl.@`Qu.og-akB07]dOGn"1H[iY<>L"+N!go80%+d<-k)Q\+q2,W)skt5Z9XT><.X,YY_:NH4_@M.h;#jfCLuET4)su1Ie]TbMs8TNX[s;:pZl]rTo@4e8'9YrG1(2KJS?C_XYbA_as`*0@)>O4gHm.^EO.RmLT/b&2Z2taY&Uo+NCO?WE9K3Jb.[X2ThOj56<7+aXPW^;o0ri@#o`SgH1RcbKaWUQf4hAqh?1MKZJsdH^6^fTiK*IGIgC6pXu8&M2JQ1RZ79.&g<'I$JqRIBA]N[dQQ$a1hNCaqKtZ"sgn<R>NY7=2K=a&q?Z:]I[h`9Z\*B8+RAQk$eZJVNeOZF,DN>Q^ak;T"50DS9YHn=7N(6E61!K@:U:NTLEr@NJY!1@HHDCuWfQrkk1lfls.'P1Y)OQogSfbuD32GZRTO>[O@"WD1L`*?Or(DQ$JoSh2Cl=11!S=NLm[GrE3T(-V91YB^&S/qY3@YZ25mleZSrn(o"-U/@(n`B)?WlP06RecEMTqCYArBHJn/8j5.kb,C7GZgK2LgZb;ak;(ljh]5Br7#P,@,=?Sqp%/.rJ16IEJH#GAC.F>UbrR6f]mreHVe0efZA'&k2G!<H<f?%qEP7bP20,&CP1!da_N`2:eI'1kQ&2Jh:Z=/aIr@_E)5=d=[+[H;j#bb-@o'(Wf<hOTH;2%cTBIB/"khb*btVU>Qa"O>B2.!(Fk4dXYpF%F',h:H&H<9UHm!\A6,WG?;NU^>U7`(48V75q`uLUnk6VZ^Hm($:+@1ec1lU3Zad&\V)34KW['*)>jGnT6Fp[4_PF?ooAFZQ+=VJ9=ZGLd0'D&_S$n;o^eJ#'D'LX?RB7Y]nrMtM3)Pehj;=dm6_=DiB4Xi>K/Y878>)qa>FcT'T8_6%><MAL&leT(jPU6>55ei?S*o4O8`-CcrO=_euH0KC:4chYkes>56[mQ.K=Nf=Wi(sbC2f7*#k3"cE^bnFEf_CV;o>6S4n@)GC\$L'u4Y#+6pA8iCdA;N%GbhaeT)g!(pUum6'k&h&[%c9CQi\9]pPP&MN%SV(cXSq;,@5CsnJUVX<6)/j[V]>_qZhqQ6F@@j>tg(VUhM7'VV*Llot>MBMO[ZcJ5e-7p2,J1mUi#2@;[TOlD8TN,]CFJXOM""aTU-X0<j*0K2!3%o@0peV(H>c%TIX3,*p`'D@bm\n9Wj^.DDH^uA-GN1oK_W7r/]B=(k,AkJ27!rD;$*1R29see"/-S&=j%$6tR8X:kif$Qu>gs&()FJ4\Z$sSM3Ci)&30r6)akBBe/M\m%9C&Aof5^'-f3)lh^7M(26,4tgY9Rr*g@i!i>N/\QXC^2DB)hptFgc?Fk1nVljegIDLT*2YR@dp;T)U&>-oWJJI,1uQ..K44[a?DappXqD8ljLnL0.M16]$/X7`4`;P3DfMP%`K,\mIn"iZa)6hbBf<5<D6*_8?5IkVI%eo?&m.efaogW'J=RU!niaY0Pa)Q!NHGB#d\oo#9D]*F1[8_N4^Zl(5\9.,:<HBhLWOFOcZU[;#0t<j+%*7dfohjpm+:+9;MGd@@Y`R5+tRgNmF0U\F]NFf$"gqed-ioO[oLoRV&%VZu@$\Wa/FI[U<_2Qi$&BjRpBFj0)0p:,HdNu<6G>W:D[V&!4q5`(&R%J]'fP';>m2eQ[sn]7ih0T6I/?p`Y:D]V\M#p)_1Ib<,PCNfueQ\Hl>!6E[4FlD;`T4Q;lTFBe@.YZ)]9T$ZBqn0?[WG$:qo_[@XAV5F6bdZ%2HkDQ>*#tTjnBRnr1-:lokQZ#/QH;`o;qtf*3W$\)e$2E^-Y,:I9-(Pf?DI9Lht9Oa]`'a(4BQ/n9*:N[VZ2Bt!RfF*`I&2o+l4`;^:.+QLW6h-/`jE_^<Q1H0uOUWTheDj=HdcgYkOdrB'0R&_3q=VV^$2khXsbu2c`q]=q;WA'P#<HER:]teADtu-YJRkn_p1`CLCt1K]+icb>/bb8@i)?<\M=_&>*FTa`0Wk(?,0%4\dsP-7ooAp#89&1_n_PH?YhBWjRi2B+>l@cP)8s#[e*cSr<_Sl`/DaaD%T7XciFi3A!9OG65=ID0Wn]$Aj7%]JP%gdl:0,.ttd2'H=4_>`jQJ^!?DgUefl>=7TVb;n)e@32Xs'S"me5Zs2'!>CG.E$Y0qm(%qoBNXk>T[E0+)W4G@U]%HUOlt6II,'p88k:%Gj,fruN41"XjJ?JkVJldCl~>endstream
endobj
49 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2216
>>
stream
GauHK?#ScC'n,h[\.=$b!f?%uV%cA':$Wp9$=m?A701/^aItEs3Ri)(QM']nmdNT.m<+B'k^%+"eF7pYHgY<-5/%*m1TuZ7\u!%9J:`lk,mCOie+RGNqtB0qNOOq2E"eGEN\`oQi0oC'SC#$"\FC1mh.TDib*%j$8s6UZXeL=&$jJMXJ]5lAcAR<LlEA<f#@iUO)Zd?nINTJZEX(.&X_I=)3Zc47>5D+Z*^,0j7Y/>N#MoD=oY[K>ESn-$)jSl"/ZQ-Sjr<%R9&":;To1NEK8ZY[B!*?8H2>8&\SO-k>ZC8UI.V&tPjOn0rk9qLn;NjJZ'Ten:NN:nn+eEL)bg8Up(@n^%Y$rVa4%"`=g1@3\Ca(a,Ur!kEfC1lU+B!tc*R9A'QI8k<&fQe^;PS<fcp.R56kUg)6sL(8F*%tkD(`"%9;[dV[@"]FDQoAWmQ=,MWn8CW?70uq3s8@5]e!)(W8V$V([GSXN.7@g'g9X5_#BunK=laDM'Y9f!J@UKcip#b(Vi,h+s1>ne"%3egsDVK$9p&mE3S[VHU@A8LntL,U;o`72"#[df#ZZA\F9Z7DY-()TskA`Em<4$7jeH)LL/u[OJ19njc=@He2iZS9ge4@;m3'S=f4kd>F-b<^&FlUO0#+W$diS=&g?cZ0Dm^T"K9Y1[I.rB"$'O>.1sS'cdHETOZaC>>bD,$#5!e7e1(@Ji4mHPaN_#rbaGCH#jm&<eec*WQ0B*D-WC'dR*,5r.N.)#=Dd"Wa)h/Z>$kTPn_5!/8=ojR3CibgI#lZ[p(:RK]>dUs*71%4rl/Ii(R;&a"fK(Mt!q^"X_GCK)h!8[ki<1N\7mhrDJLDOp_#`E]N(9LSi`LfC,c;.sM1k=1cqFk>FonG@fsr)u&E[:2$\#mZ3[.mE:h@[+\>4JktXDl3]/`D#i?tFadBaA(Tj.LRc"t1R5(h]\WjLQd23;H/<]E5UH0g2@%^RI9-a0J6Pj":@<9=J8f-33H!#kN$gI%*_9,\[9RK&C9NajNdR](&3-+d,aV`t%!2ml9Vd*iDSr[?!\T\VH]%uhGi4,*Uk8m3\0(B`^@1KbETFeeg4VbLCPmTZ-nJa="'\G=gO$TFO2klKZj"/roMd6&=,lHJaZNT(jJkOM"6(pUc-IYo@14lK(ck6]fQ>.Y1;s"Eq6^5Fdp6CnrHO;)[jPQRZs5Nb"Lo=%dfh/EY#9U$i6i[8DL^lfi(_$XHN^QCoLrE[fc6h@*3Ato1H\q]0S\T!&4U3X$rK/sgk_U546umK>dn?Sd7L\s+9=1b)a9,k<BqE$MY%cGp)m0Ucq^9".l6\?3q=0n_JDS2(_2I3%K?)hni#en$<RtC_^L@d'50S#nNL7;K#X)5hY>Ac^F#J^nD-hF-Z(R=NM:.93'H3==?$o]6*.usb>f48gMcI1#&_ItkjJ84m5+PEhnOWjp-m'4$u4&g<u).s3HTKCWuM'"K_oTbd-"K-aA7QghPG_!r.8SW%FF7GId%d:RfBSlb:TEl^nj_E(m@+(DU6u^p6+:I3TBSK('"*c/GgheOpmMLBY_CS"Xc"<];Dp`fX0'`(]nF.e0Rs1I@)XT/ZVomD9Z/$a\8&6:R3shn3V1iUZY2I<<4jkrX0g"gA^SNm[(`)W,g>+Mg)3@(jMs+l'E-Nb(60SA!+htK=G5Ma4udP7ZppuVbXk`!PrY,OUE8AS'EVI0Ut;F3B`&0O%+lG]N>&I_;[Aq]P+m[j^hX?em-?!6fZRlBi5)^A0G$2]n&WfO68Opc3X6XpMB0KQ6&!ZHa`Ta&9#3hDYhnKJF("Y:m_Q,PO%d7Sl+%g=k]-V+(uap&6;U;UStM'.P+%ck:6_B'DZRd2FhgIW8.MCo*E],Nl(.:k]s_t(=tUg#p1uXbk`bs@]Rd)UC-7MSScaklbqJ]3AH=?G/W:1I\cn7NWqHpJT7$3XGf7rijkBDUqJ0I^#V%f'*TJ\Cp*F>,Xgrd`2I<T^6e@Ep\'G91d""7cH\6O5Bmn<[J6+4XDC03D3nK#GgR^0=fuoLQ-A@4*2KroP$i?@QPl)Ad\4.qks:TCIt>B\oh<n.(tTQbYmiN\d;'F;=a!,`h%,(0lcRA=km@Cc7GT^o3kPq4C?8'f5kl/N>c48QUiPX]@&a7Peo(q^E"e;G`PU@$$d6_j`UuN+-&%;.2"KZ*lG$,lXFEa;]Wh6^&1CtQGon2,:p)`6$9nE`+sfpH5/>K'FRq_Kc[9s~>endstream
endobj
50 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2867
>>
stream
Gb!#\CN%rs(B*Z.E=mH-8n66o78_P9MhTbWdd/l+RsM=fi%H<q,V^H&b03\>qWmn2iD[2F%FUn_JqQ$B]Q<7"c8h3lq=ko=s3m.pT/Ulf,+p'SRl(A3(X^J<o_dk<_jQk8k2A'>08UJDI#2VY/ttA>I<ju"l#9\N4JKeWUlsm3`;NZ^05%E'"kLKKZ8Lf6_(t]tntO^fgrGD)oS-]Y>,Rn,KPjDN>SXlQ=@l/hWmmfu0O@T6:]F-BILZ6phV<@L[&crmdT%TNUWLbZ\p6e)hsuNI];Td'l?sUg2=oX!f;_H>Y/mE5OFP0C^XHNS,GiY5R9a35goQ_\mYuB.)kHer+2beCoM8p@.0rD$In!hXeZho.+@-c&fKg@uA&K\S(^K-H(?%AZhMI:h1Ce2W#`!B!$$"m$2MjTn?6(FmdSMABls.]UP5Mg?6s`a%("EMLn=u:r=k/['Q18@;:mum(pisj&fT-q(:L%$LNA#kSkm*RJA`Jpipr`dniDb1108P3f&`YQ%Gs/YaXO[-H[d_FW&Z>G3HIm7V,[!S!OWRmTZ^AnJ-ur>8+h(Z*nk)Yu.ne$,Na*Hd6b&eU8o4o,^IY'I/U]tn<crVhag:Rm7WkmQ6PoBqWc./;U6$7=Frkqfn>J3d?)Tg%ZXAeloaa&tm=I:F*gD+Le+5T"Z#e=gJlVcpD$irQCt`QF^bOVI51H=4q)Xi[V4pF+/s)g7W3a.jcs(-mnkF3$NdV5HV"9:X-aMMBl6mqcZXhh-o)34aZ+''_met5f:<PK_eq?CIDP&i-3n`p.CDPcCZs+\4U-N^$b;&0c7R8!+k%((0L7$B[CK_roD@b.,Euk`":h*\)WNJ[0qp_A[2A2$t,]dARW8A\(SbW#NEeBO"0+Y4!30IN,@H7Uj]4t%TY[leBJD]ID3k*/d'dM12kBPP(>,r:<?;4(dhb,J#aR`TrReEK6T#oj>`cCl!;0K#*c.8FEb=u.Z_gB3=,dk]F!kjr5gD53o[79j/es0DVWV:4XRTI,T3r:NeL(7,!U?(%R>gR^#^g=tS@k7t!$@dVTl#Go(ak2goD0c`0TK1M>a3iNLa>c2S41rV&I6M<-^>&'@^fbX1mBaO]_q?dR@U*F@=TH&87PEB]/\!]#?G;6,G:"rYYJ7\JEJRn+eHXt_Nb!=3ehuBV6SRd=ocSp1=E$Pq\U^Xd2?;GNj8Sfn^`9%b,:sI??E5@R#>a#r+nS7`e[j0AC&EqsJ1G$m.U_PMWS16R.ntUh]lI8t;8PDg/XID\7Aq`dlk"R:#](F4-^DkEiPhfgIJ;_rk:k,ZqQ'GYS:<T#iF3+.RWiHL].=nEnJ4:2<4m7fZoH#.@9J),k.C@,$?@?,GC1(t&tprtR^Fsfql#2[1uDR:qZPKt=5n$"Nk5q8K^f<Frtk[JHbep>6(HOQqi*+II-%eWGPmXDrij7&)o)%:"+:_+?,/X"]_#hE:<nTPWHUG#/]61q>$72ogPNIhHGPM9ZqXg6=&[[M^`$@X2NKes+#a\d\K<F%hXTL*.Ma*(G:W%,.(OVA(gkn&X`[-FO/dugdXOMF,[[2b*e]Jp+Z<#ri$>8:f"lor"MfJiMEV!@jeaY`<=jA[g?2X>:5:eMDVL8>0ipY=9Z13Plhe2)ZVPWZ',<%J$Y'&GO."(*;%-Cu>;hD%qY!ok*;S7^0ieoV>$EuVjGKjh'DC,L^WddT3!s`dLTXqa9@TOF&&;9sOC8&l"#Vq<ZUMjd,CqDMZBL(b]Ti64IV5\k6GlS&DIRA9YbYfXFNNI-l?qcR[]_S=$)T^1quDMY>%I30'WG+A>H.h1,;FEOW]YUSq;VknJ;qH]LW`qO:8;k=;m?G@(4>O*DtpgS?K]LO9!Ha'$Wo#G2Mi1t?1!5RnkI+$!c4\SR@-cI3sbaUPK0'^(bJN0`NFsBjHi>B@,3p_<=P6/CtQ8ni@(g4$lEV\@=^3eNIK?A8DbAeG33gD$Om=e$U[u;\]a`(Q?-jddqsfFE8dq,0NQf)ld/TKb5rVW>`*#Q`ILJjH.bT]:"l@M1Rm3=@aICTh44S\Jgt/+/>/<7[[A"[`Y=>iLm:g@-3oJk"o+OrRG%^M!mXa:O9UJ%(?V>'%Xksh)>BA!YGWm%J4EPEQ."M"i)!l'Dg-VVY?RP*Qt^fqd<UcCb45tT$jrldHg5sn2BV:5F.`io*ff*>_0@GEkCs1cilG>_X%_oNWc=pn>JQsooMVV.>?P85!ZVDa,B\J1rVf'<*2dda.9r(0E1D2d650n`ThTRGUuJ$*1&B@da485S:]@HLA+:qr*oSmL)TlRhW:H=*Z1?h3hU`cV4Sr<^,Osut&KI6bp?2^dQWI6QEL3@t)$NX*.baLa0,Hp[Hsi=mG"TJBIC*@RmYML*Z#Kb@WQ0C'^C:k\D5G>K1Bnn'SYtnf$qL?n7uX0[DYt+"g#qqQ"4ce7`<"G;(3t<_C3rdE.PWabiUR&XMJ$);(n%q^[sbhthV0e<SKm8g^lq!3C&QklP7BH"2$,3k#oUPs,jpVZ3NE>-dTU6(]lCC0n\Q=-aa]6ORQ"M/Y1k[cY.HFN<JBtBFG?@u7dtuPq#,!+7c="i9(=a6MEDQ"Y\l:l];(L6i][u4ZmRO2j,dC[A!b-tIM0*k@:)S7GMV>=Pi?Alm_OfQ;Z`$R7hErEJ-#L`2mX\Llm%,F!o4YshL&BtTg(e:[O]cl1V`ue>Zdp":@cQG4+'"+IHSt_<1&;&F&6`<N*3Me)13hl6Wosha$#+"b%X'UMJCMh8kTGrWVkE4;3L6&C;Z"Nre:\#V]:4`$V(Lafa!*^P@ta$pZs/qc"CCGG_--a]a2t>A)%1a-1U0Gcgq+_cR3Q/!@/A$?[[D?$,qsF;#J9HZj[lXU9jk#=We\U~>endstream
endobj
51 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2784
>>
stream
Gb!#\?'!a['n+tHEFGr<FWbZa,UH&3MIPni6/&,Og'*?8q_B?cd_sX3Sfq09IsoY6+Xp#iDc>6kS7'TIEb=b63VSQ,)#k!DDm:P`_`chi&L8"#?^&R*N:)1kn*[C9>t'ZnQ7OhL(0M^)Q?^]=4IaaU^;#P;FLX(_b:&u/[%l;jiI@olmoS=r3S*-,ATqCDM<-j+:m?*Xc!n<sA2h.eF@u?2(NdEeS%EFMPq1D3&#P0H+dqL=ip!*!bs.COR=uGqC9*<B"l1&!*M%AWkl)C0s-a+;mBU'/Cs[#E.ZM-;f<m&l2<5*IWGh:jGP%j#Oc&X7PnQ^.92ddIG9]]>6dn#Pk>8?DqQFq7i7cT<TAeFOofT*V/._u.[Re>Q%_j:U@mNt\-aRW7iLcK8G3]VZ:7tR*Z1&pK=[r%EX_arm.k;QE_^/8uAQ:1c;3%GP[+1X_KqCi"^H^336E>A]JlZNYEtMpjYJZDbb0-GE,i[o07]H`tF<iUbni;r4S"HL-'6_MT['&K0Ok!3r%5k0<)@`$s2JXgKA)!_lTk%$4`mM[uWV0@-g7'i@AX)!jnU/sR4eFVUURFPehbkWlZI$kdi>&?dHW;o#khJ!P]l8:-oGXGt;]R$`YY$tLJu#0R+35o.aSK"&ftpUug+0G_[uHj'5rW"7`m%YFH;?L3"t2Ms<3GLV`QMk#%68ZS]bIEBQ*)TTJZNUmEOo,VPBN]1_*$o5ijGn4<7M4bVqn8FWn[*q[4><\]k7l2QKh<`$>MaSdjgNXUe5K7F_fO)X^kAbiukmViO,%Ao3MN^7:BD#dTRU8#9;Z$do8LhDF2tH-lLV0?G\?]N-DCDfN;>E*VR/_GOq<n\>+4Cg#D,2X,-a[&"8H@&RsA]QrXDU&;XM)CgGFll3_FES(a$@pNnm,eBYMZn;t3U)a88g*`:ZaY<ZA-XgP2,/N):eU34a3Iu;(R[KgNiBiWc'Gn58ARssq^.1X^HX"7#0#2a!grrm[X$W_NL[]BudHEMR+M[WU*=[.EJ<#*Pg$Accd`@Rqa_l/mLTpCj`R><kpF8V@,#m=ah0;]5ZK)"(Z=hj-Sm^H[R?.;#A4ZuftL&D:^Oj0^)`cdsuKWVrP1$a=A%7_*7S@Xj:^q!qJE_+W<XUiYl]=@JP8s>V?Ym<chFakZBMg6*"6h]'rdCMZU/b[eO$+ZKl4Tr6GR#2](W/SNU?e9,[G-gjUTbu>WK=HG/ffS$bSF8k,CF%uPY7s*Cb/1GiD)<5d,<d1B,[\u9T(I"-IP1eP8,7\qL0*M24B"APm_?JnrVcffSq^a9kfH*,6XEXD&]Hk%IO$&an;KT-Ln5_)r[d$]@6q@^r!E?%LnA%G3;(5\?L&WtN@2'2nY5rNq!:Fs>2d5U2uWYBTk(Ld@DAs.(i0ju[OjXWeCI.c?!B6OD]`lP_lF(^&<Jo6R\?KL;9k*-Y+?(NX-]\L^!$.i3iN!-=^0r/V/?-%,ED]q"ClXH&["V.@E5J:n-f#(>9CA"hC@ECPhMnn`)Dt:FJ-h2%TUqWq>d@4]`puQ$AKX'X^aD2ch7I/Qp6.8T@sl2<;lIV"a`33%;7V@I;;t6f@*P]m_QP$R'jsa0_jMU-'4*YL',F)3$U6]Npc@B1TCVmlV1mm?HhSAjq00&OCMm0WIYIM=rh=Thilg[Fi.RS8,c/I%Y-Pf1UK8W&F-Yp7@&7:5-5\hlN?ebdQVSE/mF^G!=M$ukC@JMc=+E,6au6SKWX%a7._9_Vf\@M$\uB;nq_6BoO91rkDTNG!<f6&)g[Od$h',!`kd84kW4dQ*edAi%mMRHi8]7:T)eLFW5aB3'6^Zq&:50p[AC?oXuS664l<sHCA9CU1ht=]@6ZSsV`*t%+<]<R!B!fsg'oXa8XC$m51sRGh)<>s;uS0:8b;`;4iIAqD.%ti!.gLRS3:3OG:f!!_rh/)&[9^p9'hCsZ(:@=,d?_6I>(G"+V]q+^"W>4P-rl]/#7h7_HWUJMC!4-mAFVLnHl%@;&u0t+k$8nlEF].Ok!Y^bC_]!]71ACrK,ZNr7VKEXXr<A([<fiMc]AH^;W7m$`)J89C2lQ0<c*\qgn?3liU.jI%h!>j7ICemQu#j]0trQ\uDSbV6ZA@L)2(nB1e42cZ1oDqao(>HmZl4b'fr9=T.ib%4G+g%`]g3q0:+;/N;>_Pj8%g^`+S7IEHW.18?biEi/>j2K7sR!ZSLl<6k76/-ncL!<;h"J5qldNYs@+n`R";LUL1+o.tRNd=WljEcLRVJ("H4a0^76=Sm9O[U<jBN,65(Ne!+lm>'ia#XnhgX7t>=AgC]BN=t8/?6M92ZRa\[0T9CsBsoYbLjp9j5bW1Er+7nnfa"@^ga)Hm!D`<]!4@CY7Lh_1jR^a+nC8A&'%>hIIQ`et4eO:Ge7\`8`*bXbQQ>3Udgg46-@B]UGSa?RF+/pUD7sBg6b+jTh]')fg`c+D9pZ$Lo;\?[eK`OH=7Old>=N'qk53_==E`uI\T!k):S`Adj&pk&ak#r.6j@h#ZB<T;]+O_Y2dq&YoVXj1/L#PA8qHqDG1g&K#,[_;a4dgVd[Z#j%hFQ)Rej'+bS?_(ou:>V%$t$N!)UeDLbGpS)n'b.Lh31OI;N>+")/!p7tt%=;BD`Ih6&4II!0Et.t7q\R#J<bV,6EI%eret-DV,L&;Q9Ys7=_GG^<o:>rkd$0qWPHC+QJn<I,m^_D*>%:ld_X1f@DKd^W+?HNAogl;CVp<u#\Rn$$a40EDY[m&K5q#a*&4mX;s=fL:VD@/dq5&W>iKLrCb9&PLMY-d^DY!A>(,/H~>endstream
endobj
52 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2876
>>
stream
Gb"/'@?90_&cI0n@Lrg]3KRo,8VpDuU2]G.E17tEF+k4a^9#D@Zo5=VGKDos^V4W0.>k\ub=:b4rD3`Z%$J4Y47d(@RhZXt5N2WLmYLja6dK*G&ddBq8Rt[f2a>[`2coIOU*?-UbD`/>bN&C2^PaA`k4F_L>X`_F^G7Xl.%_loU\VRls/P=MX+%r+hdFK9^Km(\jWZ<*b50BF0cgV+)dXY5Vu28Qh<aA%7D7U$Q"oQk.3lDu(-.4rp,@<jCD&#dnDI;VQ#XC2(Ils\Vqj/?GtU*RYX._`G'#>UHlJJG@rLVXN@C,Mj@WRUDt3*'FJnJVb4&Y9;cq%,e$Q#c,>7&kdl<4$E3J0qmrG0oUna!#7UV9a04N'mJLkcE73^k%`$O@Z$]<@pR:j\JnVJ^VYjN(]"AXX^$_O_?O[ShR.pI=t%]%@?EpZViekor![8s_NUQm'<(%HA$i"UZ'oB_$H$c+jqhOV2RGRoK%j9M=CAT/n-nZmrO(u\b]6mb=9^_,f,Auk.9QepHhfAYlrQ#K)n3+tjGgIf)]&#;/oZINPS04*ZYCFe@l=10+h?Zir_Akgl$s%,tLV#Xh'\up#kC=_I>;9HRiAPMI-?C=FW_>tM*pU]1D2#_(>8e(s2%=R@1`osf_V.j]T?YPdIl7;dj2dHQ5lcrJ0U:mr3dHWu\1lp(i!sX;3gSRrMEjW:"Ngql9Z%N##3*!hjMW(AdP[rU;NRO/eM9)!F)"4p%Cq56=JDG+@6TV,%R2:\RfP&aZ%]Z)i<sn`(W04:L_`Lu'q*8cC<7iD;O#oIrLdeZjn$gk;RSkA`Rnd-T6n,kX0gRdu;HDZuEd,T[/Dn"Hft3&h66,NtP9n6`G'#g5Y-]_F#1fceDocPpl'6BS/#>Tob4hHMg99fUK/4W#IaNEJhWWj1%7F"?,`2i)ft5iW9NW7jB2LD95CU&E3u!3dh2Z!@<]uCd[A6l=AT?Km0_RsWG0QtEa>QRQ7u,!)ZFjrmA"cE4l7gjQp93qH*i_'c';4P>O<`16VlJrY"jZ:,<?R`-Q:2=A0HH$)8XG99i-0`:3?!b4<oU0amrZD.o2jUbbr'Khp.YVPGBD&27D<.je%#s5E6&JiM/EhfCA>)!\]6`tPF[6C_.r\dL19:=&&DE#c2A@,getcWk[":1D84)bIOi@d!Y^%A?@A2=/M29_B6q&40S@a'2-GW'QBt^]l-Md9,ZF,.Nd%f&\0()+E)=^XDq=7-$N10KRCTFdp%gH6LHC*W+k\iI\pJ/%*k5cu)Rd"gN.r?k<8oGE#=<X^.)\`qaC#T<m-`oU:@]^P@t)W[qYr>Cs!St6_!m[N'A!XW!7CY4X4XTd,iNH"p5G(A,X.lXd[k+f0`[AeLr40/Qsu'Y;u"%ZB:#-[A+M)Gs"")_I:Cfl9(60UfPg[C$QF$,5Dd]-`2>9d]CDVfT-t4I*!>n[nmXSJ3'1>1Y1rCalZ)d8CB?*C?G"s);g\j*!6d7]2GtJ10Y>mn^:mjcnKPL;i-Dbi#Ij_]ek^YD7k+/>[$Tp*^6Z:Ui_Unk5L;j):\2QIWK5F$\PLE.kgU^TNpZ',7qnWDI,@'Zr^lg6[fSG8"%jic]5)!(&M:[qV:r%J=fIbmK"o"=iqoi1[kn*n4DOHnL"dfB1DKZQp/u';'+kt3n^HehLZsU*M$Z2T>BaCrBP&%PD\2rBk?uU]'BEV1K#%iiL6cN7]g7Y72>*MY@Y$SlZ35&KYJWKe9To4-9K[l1cb+UH4j-`4A*#>5!7BKj?DI:Ck6!K,et=p=A`-;h+9ZeL,j-?Nk:\Lc.'rm,,`\"njQmQ1fr"e(M=aKh0`?tWc[c%8`o.mj`c2*I1T,"IO?haNA8t5^FI\D_[-psE=#C8?@<%1U"YT%bGt^D`%kDJDXdQ?E/O#+%rB6CL;'/tZQ0@2o2OND4Y2gL]"J+TfZlVsE2L:G*[bM*m0@V&ZmXeh>c<9[jYTolE"1)[1"jn)faSCr#b)Q[;G>;Y7A_^5DD>'cM]@[tKpaHB0MD)+sqG-!"NdFhX2.N#E++bR9!9r-RRr5PA*=d!<g[4fHBLU-&LmbUpAaQnCW'ES"o1'+_<X1Y]BHD^S;.'VMnuUP"3C!]440Dqkl4E'c3Ml$Tnq]DmI7$&r%hBNeEJ"B8/o-8"50f>qH?Tca?5?ZnG_e#9FImqI*?bL%7N'8kAI8O''p!(g8N!dNKUV\WhZ!aROY"Hf:_X2m"\F9S^K4?QNZTd/A<D<q4cr2*!grJJ&6M'ABJP>-/hmS+6bVleNA$?NZ@[eJiu<YV4<.^WpDj=Xqq.4d9kVl95StdSE9&L0?EEqX[if'q$0+:kQQVH<:#CDFMDhdQq=$(h.HeW8e'e`oe@M\XP'>'P"?iK>qiQ]dm<R/0h]am=KMm97GIJFfdJVA@$pPno'Oc;r7.<OM50*CjlnWlM/4SD1\M;d2H-P>>Lo#oK]"+a)Xkmk[9uAf?XbZ3sbdF'(&aL,qZ((uMRk'qLk[#P>*ern^SP))03jElQW2o!q9h]1bUp^2]<?4-%8%J),S<.o0IJ<a*oiX2fT7/&MBMu.kH9IHDU;b7"8Td2-$L5Z$cf-1W=-g;47^^qm?>FD(D;eIKeiaeqs-nnB_F2UD`ho>`)hWBVV?XqN)8h!Gbf(kQq$ocPnCXuG7&lX2<sSTYEnPq:^B16uCL2h;2>!NP"$#IO*[YXP#&<doo\SjULKo[(<T=tRY]R.f'^rW`>DPLoBR0m>U6l2TG,AD&Aa^J*1Muj<L^Q"T!$m%,]cQ2Ko.;)-$%N&(/PerWoc1Y//Pq1ep>ZB#.PZ(UO(QZV*NfF["kDfL@"\'>_%b`0gO/,#k6]aG,6_^_5<+W)?KUolpA^&%cR86Fs'OpX7=QaO=8r=*iak"~>endstream
endobj
53 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 1751
>>
stream
GasaogMYb8&:N/3$k/hp",S?R;NqO\5u$YfD$hPfJ>.R$<ofFtKK&?PV'o^.1J<Rf*B.Y`K_Aa7biR(%$-:0E_#9m+7)*R%mQR9dUeOTMj@-G$8&&n1O!AR'O2FschD._$G_PT19VRn<^);2N*C_p*&LDEf'uf^krD_3PUQ`LsB4,_%1?V*BC>ghfMb_9$*t&,6JhI6SVjtRLD(;!UbB>8AdaHl2p#mQ(,S^$[5Nr*=ck#/ciP*^F2CbPG/]shck*@otB_.)^STiK7\S1L"$>SujUt8>38mRWP74E`'f$C^iqFG>80!d!gYuisYZ?CqDD052mrW;MY9YVBt6rL2uIm@JhV\_NC_%Kb`g6E8Bk+'$j(HHbbpEB&'CjJAa`!^*/j@TR9c''iA<lcIZK%NGnW0G;`h$M"q7b1VW@5Fat:08-4@S9Urnm#q=6V-`5b1`tqS]3/)eJYbumT%^RqX[eOroAk6ZSp[(E1R4I-cl_s"^uccabBH60k>Eea^6XuLh#IA]H@Q5ADol/^o(,ET6il0<0aJ;Q,^B&N^]mD4aXMA^ZRp$.r%03@nMf8G\#W%b-e2/U!]K<Qs(Q<3ZG=`R11F1(n"RXe4<fmiTU+i<D>'IqC6`88qN"emAt(p+b)9'eI!#-07Y`WGH'tkn5QdcbLD*nnk^BiI?TtVOUPPGJLV3r1:adpZ8/:u)gj0d1/jK4f=$[IA=IKKi1?4F("t-O^]IIhb7&9)>n3)I!F#n:855-cYN-&[c*gT*MoD?]_IS184.Yem@EVZIC^!QNC2t3tdE2i1X3-UsnhA`!D&gS-NUp?1B];WHgeMQG:V?M-KDS1\F&Ls*RRr*@9e']YHB)M(!e5>;7u?OG!Dq/M%F6=meWuli3*:F+CZD<LAQ#QlK%eE)m.,PdDB+F<o#.*=cAiMO6'U.56W6c9@0NL_4W4c`9_8X3jUbZdH4QmO\tF3BfI<Tl,b>=+2@pGVrEF\=QH&OCo?Y2_\'E-#[a!u\5Iu+8E'(GYL&M\?r7:,0Q0@Mb>S:N`k$HTdgc.K?rJEAg<*K^J6JE`8k[pB_]#1`?A:Z9eoLE&+V6GqChCptCj%J;n2qdp["D)SD0!bZYAoP@+EAEuh#L991es=`=V<<0nplCpZ,\%s<PNOE\1Xj4]!>T,I2lX!5(!p7i;P;W(HB%?7>m3cr3I<*4<L)lt(:4::Wt3@X'orB!ZF3\p?W,Q\(.*AE%i9sn%Am1meh!-t]#@V-RUNErkQ0ll`%aXM>FBnHq1<OM&+;t%4]fAnTR>^G'a>%n(\j1ZblcO<-[hm_WCOV5O3Vqr`2l5@l2pLfSh=1#nrgO_5iGNPPY1%N=k1^l[PM0d'8I`@-V7dh3HnS29Y!'fXXIIQbYH<=*^,^[^(#+Vc_>I-$/.;^k8m/%Y"\j2\T^u:Q)fo#2-mJ>doE_EAO.mf]O8FGgjEBn.p[G#-:<Jle60gffMMu=j-H2):P7#89q`G4Yd-d^1FM4N"qRq>qSGa.f0<,'J4dMA889KfQ&L>QBEM*%pts!qP8-Ne\7Z!elrF'nHcc*B`h7p)$-shPHpHone];sDqq9%bB>0k\_I5>AGXqA^[(#NjV@`?!s7N!Y<Z!<RKfi$[SZREZ9bP$inJAk<*WJ=:@.c;Q3Njt,)daYhC'Wj$r$MmOjb2C#^@^C=7Z*AX9_A?s`Z_YG8Rr[0:3:'hGjH@7lM*%fr%qiK-/(M7U(@ZrF6pt6QFcj/T1=eC]D#`%UON:kS5`J~>endstream
endobj
54 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2989
>>
stream
Gau0E>Ar9;'n5n\3'\K`=\&sVG6[7uP-0#b<_]po9*)edW0,"-0+*KAU4;(h$nmbQ>I"nXMlc-[iLJ)8XttZGr$T_gPFUjs/\Sb/,TOC$Omjo_DZ</?hHkTAYTh\C@ZRV3$Z/,JDr?;?:Oi:c@JR:B.*2-2oGu)rpET9odEP+h@>Hen1%)KV4:qgA7$cGAk1_!aWn.*!k_(]17Wb-Kj?pB3aG$YY\k"B`F+TL,4o6U4rR\:p^Em-MPq$mEd"ar"H_'H2FSdHArk])'FC$Vj2op0\b-_\V:M#ZeWZ[kR9YJKI^X9`pp6;q+[@Dh)LdbGgBLeSQ2g&u\%No)eomc%+OmnDIIt;&*eU^Gg&3tf+/KE^SY`$CW(1atLj*U;@qq1!"^@/3E&g<ar&T$@H8!upS7Q27iMofF"T;:>j<EAPO9;?U"QA'c1`?RBpf^@gF&Pb6pXW2p:j#=(WpsBC%=jjdNBa[nCA3l>(hSG;.!5YmiJq9#Jq)2//5#$TuF'@3MAmlc[rE]Y9a,phG'ukikn:V("k;7.(fCt732bfmeC4D,S(Bba'==T9F-k9Xd!5AVJ"YU?1nfc&4+"B^[?S60$9.PjU3npl^L7%;[i'm8fD1q@s^pTQJD<qS\C6e'ol*$NkSYp/].=+q\1t?.h1QkqB>#Vu+90`-J:*esIf.nq.;dM'o/t%*&;OoSIZV"eliC[W\mF,N=pG-O6qqc:UF]g>@BpMUrC.2]rmD4Q1?$GR'p7,/`RH#qTN?WjI]<pE;^*q$f<=30_Hn3Yq=%,80mYl@(EK<=W"D3r8MGd0l<$rQ,++eKQ2bEUL&$W)nMAD2kHEHYm>4`t0b,0]TPtG#%0,L%NFes9BfTu-K#T,N4.@>/`d#Ecc/b'%g_7S[6jf[H6#Ca7e<1Ri-rP.6;VSsV12X:foFc].\EmM`O\L<r9r,>9?9aZn3<IuVjlP[Xm,Vt++5p\2Q@FDtoZ/a(\q@uK'#EPD.Q4QpS_L6X1!6#iq+sd7U#[.<b4=aPL&5,rbV>1/q@sl=dg-4lJ-N3H0dl#mj1-GC*h*aqH&_t'j:Kp4&c$gh"YF8K'Od3#k?4>Sm^\%H')b1J1G/MbG7s)<pdT)aWU8G:u3<OtkqDt\#)?6`54jYakB7k^i$:8p3$/P(]6Nk5k9u:WSk.YC%fmD@'Vso==bu-]H_%oHjN'6BebHLi@LIFULfY\*lITdlW-mMC%ac^L]?c&cCOYsB@]NWRkR$k?:;_G@t/_f>uHq/*c[Dh!H8DT)maRVPNO,!Ca.]gKbeoI'A/QGXP,o(:YhP`H29+b8\IkgFDY\EDF["KseKA!rd7_h[S$I/#)7TM4J;S(uE\Z9_@9ArZVhja3u3-n^Zfr;E[P/^b/!*LcfBnf_jqOjsi)Cqs/5_2:pi*^-$ISZT=Y!/?1+CNo"\8tR*';]s:,@elbK]W!d/QD+aXoMi7hrc";>\\!.o\`-$9B"N%-Uss^$b3g9U?WT#'=h-#gX'<("g%`3VZMCDJ94O,,,7Qt<qV/=A-;4bC&t$8DA]m7?););_.W*UIXp's,0g,is8IC3n'gFnggkYYiqB*#l+!SC%k./!ReH-d0>BVLB&"c6SEC'N'^?N`#Q.ULE(N4RH&5^8gU#iJ]Hi7K)@tkeJD+ff-d*_qPFo%r=.*<sPsKoAH0c58fC([_m$,/k+SJfs=`fAf=ik@*FX5<mBYEH)SkeKq`Q9(,I"trW&*4-&/(!Os4JmuS^[2,>hkh\o>_glemrICBj?L5Fb\uZLR]]?lmJ9I:['GmAK;a*\^J##_'R+bk)D+6_Qm"2lJa,:^do5\k,*Gs/gUc/&]W$0CMJ0#IAQtkjcA]+4G>?VW<fi>%&Lkf*;;%*hIq5hiMAfQ@riF;#9=7b'QSIPnXfAhRejrj\:1[J1I@B0ZD-C`p,f:k8D;&%FZDru/=`8?%Oe^AF13RGRP^-_n8PI9;1E=ga*`cj;F$b+$mLS18]WUjPg4)>[oD/*Cc9$,Se4_peDVJbYmWqGT_J@oB_T6d%VlIgXICK0jF+#P]`s%CBHL4d1V#:X!b_s4KOn4s,(mM8A,A"IZ88k\8ms.^2[sa&6H.leR]H.[UWr6Atf;t%M+#%OCrP1q]q\m9Ng*?5r4E[mKpch_aS-S0;0;fe=*#AKPq^a,@'@p:^h!e/;]M=9M;2Xp9X,XujX^>\mQ3B$(WYi>Ib,"rH563Ck*r9R&dp/JfgsPT6`lqEikq+gtO/KEbf'.,j7Jn"Aq#h+>C9/M0q]QpA'G)I7V'a'+#)U5_Rqa`^[O#$shh@e3oMapuj1!2P'P0r@W,KK;,C4_i_2m:UV72!H**Qhinf1t%3!'cf,[-tIGSE&Q\$n3$SHO=f1=@0oTZ&klQCF'0R@Y"mgY&eK8,RE^GgQdj]TY%._?)F4-Ot)j8'ePrDJ7DmS;(Ht5Wo@i.,ma0?uY*;R.r%;(koq%;V.hm^YSC!QfKUn&H_m^oru8L;\`PikR[Le=P:MEMYQ@B&7_5`#:EpsKuO(5(-Mo@3&Wf,6nCgc&Y?jJ'FmpG<)oqQ1W0'#P+"1IF-t+N](BPDZ]8Zs`[Hu(PgA=5nXMcR_Dq6LNPR<=r`$\HB`&ks'I<Yu$EVhFlMX-T\$X%=4.#2CfduDgP79rlH?AO^:<1rKlLQFPT>A<ea(PKK@5&%DoBD&5@,"X'BHWSHaZ0^nb+/=s8_7PEFis[2_cr'U(lVssdhoUO)"ZPi%e_k5!.m50k<#"WfpHR+Xs3nX]h0r!SgRR7bNWGs3"DQ5C.udu>F"\`%R<,Y_C3j)!?iLq-4qWGlrU4WoPF8K\YG.I=hWK-V["L!mA9a2eJ/Mj;Ze&T)B,GD5LAppDNcZWn`!g,(r_BY1f<Eh:P/$*KT@J7.hI0h.hKng037iJZ?mshi>RC\(qWG)k_L.e4V^`pean):Sd$Z(FAt@3<'0<CGj;8*fFdZ#dt7S5-TGB*G]?6k6Vhe#gE"mpk$"^sm\,R=!>aMYj8~>endstream
endobj
55 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2591
>>
stream
Gb"/&?#SK='n,h[\6*uQmm:X]/TQE:8CDhCD7=0s"%<7*N6%,<1!*:)aCpiGhfFPpU)[BSG5]dC[:)]H%Hi22Hd814I/F3:Io-lm\YE4b!<jY&XXT(>R-srCJ%<2dGi<42'':oo=hOBj*3X(dN"c'NNu)+hqhp2lR$L<72'kiVhGs4I@Q8=`4ZG/<Nq;6Q:]66bGW78EYn3#Mn,pMbPWLRo]:,m/=1bS:ad-h6_P?u^>uKTfs-7L$*Vs3m0AL4c)lj<lh2(?(Q2Qa251&-[Cs[GDO3Y_.D_k=Smju0&9d*4u[Le`%!FPef5"TggU0j8K!g^+Dkk;MEZSXm'ni]3kHc+82&0"2,3nsQBM&gf<4tVBm<PY'lf(s3mHMFWaiDbg$+c?.ErjRj_'X9$5AEHVqpr'3U4RqZu="e"@[_YHaRoU_CQF*>X>"eTkU+*&W&!CaA,dgiJ`E!gQ[*g)1?.4tBrSD]J)Pk1Cn%W)R/aW_U46V^YB75j$^jDIPfrhK33BUa7-iABPgDjYZ*B62pq"ZYZ@JD_*B#!E=Q$6R^5Ku[t"$b,9dgO#<L4p`[Jn=eKqr-2EM=^aQ-Z,o+@u9e/)S;?USu[.*:1hBd8RX:5J-,;9V6g2U?#K/JZJRTf&GP,Rk]Yc`<nBF\*,$jQ!&W4R;0<N>==[TKAV^+t'#hmd=lm<h:?np[PuU8\,h8RdW(+OoM]p3qOfq>_:GuJUHjIQBKcj\D]t-,-&hX#6KJ<_^CrjT333@=[4M)RPD'eGD3fpJnB%p@A+)%El\Q9&FO%,eMd5>3!_'7&8Wj.Mh8[S,&=ibn8bo#.L[LcOnjpYKad3?a2VtSTD0B'&`b<CQSf5ql]i[>cg=hmZ<GN_Q!2jL35W.RE4E`\*W:^mJ>FXsK6r_O\#.ERcBQj(O:p8Zpm&U$g<77u-Em!/V;.TFlSAtrClFGIB%^o&HMI,]`=cZsl4-d+C<Cm:lYR8ZA41,\Xcd2a>5K6q%LlUpIJ/qs47V]CsLlQFe:7A\\Db:*"1=q13)V*6tFQa)m:Mj)[qY`uDuBW75jZ3YKOMCgjc81^-CAJ%e_N\tiAF3[4:d]*BRhucWj!La1Em)r"#!piF#.qS%;7;b50h[H';J1+fMNgP3:'9+^=_C,qI'X&s7Q>"]sgD'FSoW5Orl6[RE\RGR2IN,gRP0)AY[bYPRqBTDD/JlSR@Hc&AD%+:(o`H.N'P+X5/6jC0(DQ/XD)i;Ib3-$A$aM,hIU*lb8N-PC'.&Ic6,N=.gDQqNj&McD7=uef41MBY_ZEtPG?o65Z7-XkY0N6qH+eEmJ[D(#?-K(13#J^@L:%92<3'A^'1P-$T!)&%bUEk9JR1+9MBA"JB5nWi$tNe27*I<Epm4*M>iQ!\=F^?.l5i[tji#<"6":M50h=;d_u=`Ib39X74Ki&:S:)CD>Qcq)JCbIr)MMs3n;fZdGOpT]&@]SR?9k#8=EM0G2D*P\@gBq-JF9T\V.Dd&WO63+);1!p6WMce[L)!L-3*LM)L\/1#0UYE0m(R:)RMc10k(4T)l*-I``cK9JDA@Y,W9c8^PcO84Zq"m;g_Yb"I#K',+oq3^&pGQ($VkNEUX<PTt,m#5FothPiXPGWP_:,#Kq1qeWhVTXIdcaQ--[=FOXd]%^TRoB/r<snZe?:mJu3dUl05ii.I;3Hd:(*.320gHJZLX#sn^`3!-b-\r?R+da*ASoRQ'FA1Jd.Y`6!*>12f[dmXfoDN?4$S-n\;&E=aH?9f<1hNimmpCuB7fOS7iJ`a5<fH$cGaNo.@MZm@2N0AhOUpa]47(GR;/9Ieo%[(a#\DZ&W8ERPX.&`K;&!*IWB7O\+4!WA*0P&<i<J$K_N/[;:6[=OkS6W*aTe`HC4j3FeV(kZL<YUuYD-ZG3>cH&>MoiDsP57k^oA)C))bpDTk4t6%)(MDsjFqPbPoKa'4UhHT+AQu'ldHX,];sZ=?B11j`9jP"NnsM?U<5i[=BWoqq^3]jQa:.]&4bG)bSg!X<I<r-."We4\q\<"l;rSX>3I<=1<1$QmP'e46QAQ+m,6V2g138XLgYoYpp$'!<@GA$E+7VH0Qmm5[^4R1JDb^r:OtA14p@C%-Hdrr;%ugun@KtF.S5R=,6)RM1%LOb]gqDI>SqqUNA::h`n6>cV-D]4"7sAt]A,!YeoDQ:pTWVYbVKoX3(?"H*OkphLtgh[3**%kmbO"&_-9EEE.%,ofUc`8XLTmC\CKDq:<7RfHM4g%CmetqRuM6[l,R#hY[_,/*-q112R^;"\A._*1bL>e`&(bKe%<J_NefY0iF=]kkTMp#hd80:VocSOTB.;S@G)R%)0-:=8^<l_&%A@Do3("r5a:__(1<+iiR`n.\r`'.'.J@p`nG4ng&(?58Yq`dQX[Ff_XoHIdm<YT(>P.J^@ZG$q]8HYCH"_uoNN@gDGWWG[\JF2Ip/:IppTp!R*\i/ic9Q$RVF>@=T@>dh),U:oABVih)A)LM^]<df7#*2m7bH01L/[2NF(Q_WE^TJ7R,fpaEW*tdZ!`6JAjPPeXF25,d3?kA*qGMSS_XIcAP[607Oe=h^2AijM-LQ-0N2rq:/ph"PG2(FR^GEQKH'~>endstream
endobj
56 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2731
>>
stream
Gb"/'bECW"(#@2;gr25j4!93r)bsrf.isrq:D?IW\4W5;cm0ccBW<!gC:qWskM4(0*6gikC<Df1Ulmu$]'oNfF.7a_r"\Z"E_#c>P+Gqd&g8jY,[s!8jj3SZo'GD)T1;IT`8p*$(*j'TBpcjG]m4nc-Zh=`.>]KH6J>;"jR,r6DpLn()>6=)0oGR4;5?KQIQRs1!\=U4)a5B6UR],iQ92[&hX%^lV)iqQQ9Mtidu6]!p]k+()?sV*/6lqb>$I?c]Tpa$XmNU)Hr%rS=J<&RSrAS?gJ1^:J^a6X\"ti3fhs`nHbB1o>q9t`jfkm;&"9cUlL)0*U?PWj'_js$o1%.-OrHh645'N>!^#dE"3O#l/9%g^.$>9a#s$"Wr$Vr:\G.U=!C\!Z*?lK?W$0*rV<fE"l.)55=mE`g//_HfqHC$?7CAtOd>,<hcs#-u)="Z9`K"`ap<(9373tuBCYdFrhnCGj<ju.KH1744BeoPs'R>4\&^GK*`'S#!*>d^[nj-),]&;@q'@6,%Iq-uZ_S?\sTm%<DVXlY:niXU[[F%&s:I6^lK<'4REn5&F-bl1th3Kn9-bbrX`rSq*.JA+P;]#>fDE0a:8t(Hcmi2EWh<9<oD/N0%IS)SkA:?e/]WmRlQOqEYT:q\Uf'%`A/EUWXV62bZL1,]o\^GmbX%iQ"pr$'/57TmQ[,d$9];7AQOmQ\WG,jYu1IeRT_0>4n;Am%8kYT/YrqcO%*OPVBeVd>nlV9@f>=GEtC^iIsHWaBSS`K=X2:37+0/!IC7$,;'Ejmp#c@TU06R4.Qf%Nr7<)n-]dotD/K3&fP(;\\g9%a[r=B,sQ;eC(6oH11T+cpnL4!tbpAr?d.aA`o#/u,CBr%KTeOlDeg:PLb>gaK,+\W6uTcS"8Bb_6GkPf`?d(Wb/o0"/&gF8fFQeYeG$7(:r'P'1u#[]aFM_Hls4H$h,@Y8nM]F?7\Z-Y!W=a3J(*7Aqa'lOZK`d7^T#M!U$hpXPlfiKuBIA-jhi\(A2DeRBh-gT#-0=%Ese`bnf.Feq&4W9:G&(E\"WeD8BN[o/;iF.pA]O7q"DFkJ_%_!b!W1Sjc&ha7%Aclhg_Up68CkfOXGUfP#^I6.Eo2<KA(\Na-6_mp5_Js*d6Opa6""uu4\):i!JR5#1)n1^fGn'1uYIK0es8qB?bE9<t,GUOIb-Oila+a@RC#'UZ#_TU`V&e8PpH3W@&f`)Wa]t[)&On>0o416)(-C*/]E\"u.L#BJY]fSCLbM@&,Z>^0'f<OH(S%.Qa6FPe?[;fp[f^$hJ_n-<7PXc%TAA,..;n8$5CHL/4l^A4Ld:Q,$?nh'@Fbf-U6t1ut0m!Md6\C"5TWT*7?bU*EOra#$c!UD9eLY)giU7`=4m$#ia1mPNnqSZ1**gkL5U<D"\cQhPoRgs"PePs'9JmKj=H!tBrZV_h!k=9l-d8OUNF?pkJ6\2qLc5G$U2=0HULRp::`k#q:SX:Chd)aBJX6O#;]Y8$q4KdhVcH*"h:9[8.8ir0M;**tm,.mO3o2c8mRVKSiR2DqXF7Gg]1)!R6,C1()ckkiE]&Ne40kW6/7]H<WCe64<*3("RHll@-1\de6gs_sa$\OZj.(3-Q(ntef#ftj*)#@b]#-3kHXrqbEV/P=WbuUa7=I-u<rf^Ii,KQ>c*9/Z"@`E,Irk-IJ:#j*/&-ISq0HH;ToC*cmd-Lblc4lGmMIaq13T\PlG6-&HQXAs^s,!B*eaH61j*C74+_eB--5IEm0SQ0LKHra05JJ4`Zp.Q:W'WD2n_LlO>@C#hP_G3MWNg_XS3r]F<b"qa:WEZ]0NW*XF:>I6q-g)dD&r>M*9r,YMZ<N/t5=qh,#m"DC:iM*R40.$8fsA2'9`W,Mc2\kAtS^IHu0o-<[%\]3uW<FI##hd&P-<!hZ'i4QjT;0kA1shjfGgc(97lFH5<if"ROJkPbcqb.$FLK:q64N#cKOru(_.0Qr]A:Vtc;@uQuWf8L`hl+N#r7D[G-G3Tp6.p11b]%M@FR1k6pbV3:bC5MZBDK7FGWHW3!"aX?oH?&%[$5@Ng"FEE+A,_0RFpC/aO6!dd@qOp0R@PsZAM.Mj=p#QW"2G$6PdJ+AmU58W<k!u#)J-(*)^fH*)>'Xr%S#jq!-4%6pL),a`paH_3;%X4$VYFi!^Fa^,`7lm&8:aN\)#?W[fJ[PpS]bKN>HsiENnG?Z*>*T"<!OgKQTG``bb342TS6IBJ$&82nWSgD3,\_?79F<$ChF#8oQ-`MYO-'o=$Zil:ZnC0FSok?oEtE'>/QcA0qA(4ll4o:W)55l,nGriV!l0-oMAOYG=@qFqr"4q19r<^$V#=THq%C:N*cZk7grrp$QS_XC+9f2==elB8rnLB-;><]Gl4X2/(eb#L394O$_Y!-delH^)[CZSf>0e7s1ZbZu-JAs!6?*Jg$dB-.a!B#75rA;,5=Dh4r4FMS$hZN^'*t.63F'C(5e.-D9V+/Fm`3=Vin9K'F-#Qf8$!4ACKu2%ZI#>/B!L=aapgS]tU)ro&^aF.HjO3m9;1cTT>9A\!JURVT\ECtPbb3\@2GQ5bIc4-2k^WBL8l_fi,+@-$H4c@n`r<gLWu:28Z-GJPA[P*Um`&&[iois^RpDi4c\6^dh6!s!PI\VkIU5oGl1h,`HEf40+iX$'dqnR8QEm`X3nOe#<eOQ8F3/0?k5l)6Q$Jk/]]!5b]0>3\hs5eVB;rW1M!jrYWD#DlL^cQ2E$fma"`]V4i~>endstream
endobj
57 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2859
>>
stream
Gb"/'foFh.'n,PS\/=i\npmH;>U4??4?-)^?tYYHdLQYWQP*;]C.saHMekiXqOCd/XkV[S/B0fkL+S6Th<j!E:6hIPItdhc58!kYSmL:\&g?*"8]6'OpYXD+mVb;Gph>tG=\O8_YCe+<k:0`W$2sA<NM"SnVPGK7FV<,ZOsIHm$Ms:i?Z;!;Y[Z0:kJncN"Y'7e^K;-,JtV8A08SI6]3n8*-X+/3lD*.7QJRn;:Rc=2-4qg/8pC:BK.q9]m]&aA7d'E@Pf:UTo8;scUAM.HT_0oYS;TnpAu;<<>'aD<\S=_l\Lc7^\Fi@<:sF]7G?sSu=N8=cC8Yi'9CkTI^^jIbY@%,fGu,d7fu)\lZ,>%kJCYo5'fakj'Zg]-#s$%Xr+I)tEV:YB!C`O0'/CQE.@4LP9=@t"oPRIl;8L@Q/^"MBV4gAJ%u-l7<N]o6G')=&d68lJ]^!X?QNsPa<7S"2p4k2CPfm7>ZCjNUUC7oe'Z#tM<e>,C7hK9G!6>H3]J!_;euMSu8Ga5,AUOhB/-PKqb,]+Z2m$ZFb!I<2#bY%:WclOle>NG/4t(.r)F3iuj/N>dK^2blDO!Q3XY+^rYn078'oA9Nr$Pba\gf_u+hYd#QYc/F(IKh^K'>FFn]r[dVla\^&g$_mKFch?V;&paC"kjhN`FO\>Lf6[L2W:&?Oo(co0lY#gbW&X-X4.*<JfVH5IJ.onCu=(l7X$5b)9_>So?>QlATWNqL1sV/1]7s<#6SG8FL-C8Y@$*Y"$$GFbZ$iC[r_)ObZCT[RBE<[E9@F8G3fJDj1EfjHZ62(/ME-T8euMp!M1\fMp\c#\u0aq7bT(q"e[U"ue]aYgd7@=PJA`[VD8rb_8GJ'm0_X3V8k#,Bc#(WSEWNqU2.4L64.'UpJL),@"PIoJF.!o4ftn7&pNk5Qfl8Bu)[kHY9D&^+%4)>e2>oV5hsuUeBc8,0T)A(k=Bup2"aGdNGI1ed&_8LXKaoncjUG=9h%lB><2pCa[nV[4R!_)cOSkgGaVW1G\rHAIN!LEN#fm5j;Wkb9Rt[En5W*A9$sJaO#%4n"QKdr@lA\Z,5Z2J(BuRK'*[`GT;pmk3KX(G\9>:n.^CWp4-@N^en0.OSfg8Hr%3],huQpMU_n6mEW"WUTEq7&MU*hA'H\WY-g>mK4i55`)3X\`PnVD;<LG1.29[-ZBVr&)Laq7W"PC$30&_2E^aQNVB894nNsY+ZYg8'>[!Y,g30C*KqIed[ZRDcnSQ's*PYiu?s2r;=mn3L.B@.oE$S(<l52?6E4fHIE1MQ1P+h*tON_^#^E0q]j<rPQIS5((\,BAeJUQG#BIa5f4-IKY#`PFNW#tW3!&t9Nk3b&#PbnYJ9'og!0bh=@im7E"*rg\8B%9Ie=KbNe2a3YO95D[V#p*@XVC1`Dq+KU0dj61Yam3S2PVG)d.(5(.=4\;Z%&/egeOm"EAmmU$4GY*g+'2rtOLbRQ0a.28BmI5F`50U,pZ-Xj"V^(u<ooDQaoQak6jq@!)Y7#4aM@ZQ6_8Wn;4[)r[<&kC[dCdZ"ta7GdZ>N]Z.o@4Bb'E3F=?c7<"<^&^Si1P?HkSSh/Fsu.'="gYbUkf<P(%6aeQoC[/PZtosb@LaG%K]dFHN=NUGsQ[emqD1KP'pV]TIT4N;5rWPN,<R50*qF.7k>q9^GHFqo=;\t[l6.ksMKeFL7NqE]#8#]aD$BB7)7?o-a;gCs`u>chPYiC3:4?ZaCC`1'iBS_sZQX)U"0DeBa>8I-(6FooruQ7YS,3o^7oeA\7k1\pn1CEK!%c_qbL!hM0eW,tMp,JA>pM:G:Mi'Da`IPumm\95fYD_]oAP3c#k#:gu-<)W_3ZrLCQj0hJ6m$8L=mH#2r7a%:?IoK?@$1p44oiqJW%DirC5]'(DU5YT?[j'+FnOP2?Z>7I:=,0*V8&$:T]::Gj`\W-L@bhsJ5KE9#hmsFE:,X1F>e(a5\1=P'e4a)S7GUpiCc3hUK:#e$>NsW(^l0Q)>&aV7RE'I$cbO(mVs0m5f+lhbZoV89:W,,&L$Ng7Z2H3RLg5RWUR!TkFg_a%:a4X\+/C-1gDeKo>l6&'(R,+XM2oJ!Kpc7]0N[a=X?%MQ85I&@;KOh"D_IW:pbCbT'pM@4Ucf'->q/79pqKf',uPlnim/e`dVD`(rRFdhbee"h6F^?M5,jXgUr$9[)hdGsq\!d=9:=gHo#103],mG3d)UjeT(rU^"kN/p@RR<]nPW_P:8HQUPR9VrHVr.:M;D0m"1)Tpf"$bR0?V_*0/nf.`h(D!$7-W>O7l:jZ6YI4md-KX,2mMK4F&l/C4biTK8HmN+'2akX\8hpA,Qsh+4oZlZ'QohP?aCYj-Z7j)@bSYYS![ppu!j$0_U)DGpF+m'RF4/4;B*0VktF4DuT;#*KU.'6YY-W^KJK])?^=^>(<ik=U6YoX4c;6/br3hSN4WPN8\@4U/=EEhg81PiQ^A8(f;@O?8>0lh*9^RX0Bi:gc?!)U[ddk[9!eJ:CB?qG-]6,OLAE^9&e?]S%QhTC%6nh'Qr-H/]\IUJB(AA["-oiK*+0`Ta0l!b\3@[Zq"5"HWS/5F*o$ccd1a^9-$TB<N-N&r/2(Cn;]qd%ee>JAHd#"28TY"j/jeh1G67UF7ld?CP0!:!?&nEQliMBBcIM-]J0JAESVd*AU^$`Ct][Ap*a\1?'r^l$nAH)_mq)9*j,BS3[dhZQA-)89nEGIHJ-i0O&pE`Sn[bX(96*BXZYW.'7N'H#S(G<J\=&uQrTY"5)_j$nA:GG18eTqp+n2;BF7"$83nNr$p>&p,l3J4.NILD0kOk4,9;t2rH&B1bHBOu@+Q4GrZ*t!@'9NQL.1+):b;&6>)pio8$I+,?bB]3+T~>endstream
endobj
58 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2144
>>
stream
GauHK?#Q6&'Rf_Z\.<k(,)dDRM,[JHe8=#BD:;[g.f!Wk#4Efg&-crhIsoW`4r,N+PI+2(3UFV%5L)FdSf9s:IYI_Zh\3]9V"9QgiR;@0,'62`r0b:24F)/1VEs9U+h;<SGYs32lmH40^OLam7W`uT;\W+Bq6[%J9'rO6r]$;S-9)*cfjrA;72C5!\`%'Mno-rmGKhds.4AscV9;#m^8TbVgo?qulJ/3d5>FaoB0Xf+0AlArn]%Hj<,H_P05=W1N&FJrndSkg@tutRE"4L*@U$AM4R;63;s10]alKa*cgg3<\l%:7o'sFD*-fKJ]'5:M<h@l3"4-XLKK#=u9jT=_g$8'B!'?g54\A,".PTMl(JtTGI)]9M)^KkHB(+^=;8BF(JZt3.7YlaMfdXY`77j[@RpS`+g(4">Wod?)eF-pB^PkuIHY&8+`h?^=($ub#&k>p!8E*Da1FPW"]&/Wa<N]!QS+#dAn6Q`I+Qar^/G6dq@:OLM-q"\tO@(5S,Qq[W%Q5tN@Dd"UH6V@q8OPgj>ueJ88_rK#'riB\rYjI'S'?1;n/[X9bMfL#iVLsXePc^0:<<O#\fnCq]"XD/oc2lSZWrqF[8U3BB3Ue=2:eWX*"g,Ia[3BUd#^E)3-Z?&=`fVJoM,<#0,k%MW*7QrSg7GToH\R20O7g2<S&6?FP=o"+MJ)Ka&4d+BojFR[XM]cR+NB7>t^00Ci%j1-gKN\qZ@_$&"W,G$soK*ZFa/fJVLa7ZI46+I'THZm,"aKDC[TZh5S)NB&H><S#`G>rRl:2FaZupCiqB]\s8#GKthI5r7i]5jGN"TP9a@!Q$M3pYd1bAHqN9uGM>Db`J@7P7,4Wf9+BM<9H)3k)>XsK?3-6KBM9P]4eUlMP6FHpW#-Lt".lMSL0krAZQEtM.P8-@Rc+9uWhJA;/CYkaA(j]O.Wm>Do2=1TZn!ZB6#AIreAMYp-(2p_n8;2g./0uIM3=i<<XjW=&r'mdb\_=5$0KNPr?1]#N,+BE"G9#0BL#KJPABf8^'WtH:?`At+aBIrLsH4^C6.;R>Rgste#Em'[D`<E/Cr`sM$Cf,_pi[<h.qrpYaR@1_mIT@iGWG+RcshSO%<[&NdJ0Hmu/lX!P>m?7iq!m#-Tc;/>Y(cG0Ot83cXKT;"(r+#I"Blf@$<>-+b)hQNDLlJp4.*Eu5D19(r5#'L-]Y;HJ*-G/I"#p2$Ve@/gMQ<n43<)?lC3ZQDcDn:;ff3-O5?OLk43omQH::W7<OVYKBNjCW*C#hIYX%kpd5.Vh5=YWeW:!pZ,u:-<<%S>0,e4ZbM!7B75^;6Z!gX06DsM&`b&5[MkLB5oW+8STga4+oCNLPlBmq%8*p5&0u)(t]8jS-,oF]X;lqms+SEGfLKkg%qPs&+iZU:\fFi5-a/rmc=]3bg<d@3n*`Wd.DK`?_&*9$p;LrJaT5udSaSF`MI/=j6c7*;YC#p<;Od+?6gUoH/[0^@-.q5mWSmT(c:j$Z54T@i'.>cEuH'ABEmakUX$2pXMu\c5i4$7&A7S^C0+=U<JaqR;l4Cc9]mb85YKI@drbZRgW,B]7?"akA1JMk^5$l`$TfTC<0JTsH;^Cn$dK5Si&Q65Q@XuOm>bRYp.6)]d7VF!LS7((#OSPYJB3BG(9OBC_4^1?87Fp0$JX9+eIGm!"(#RP"Q9NG^0iN^.rAQ`o's\e=A=cHq]lUj5P3N:2$$PU44im<m:T'3OMSYgb&)5P0lkn8e?\DEqMk7QM%c]*oj`Y$adaVY,'KX#;_4+ngn1]lbM^VVNYK/EYi(JKZ(sg.\D"RA3JJ[`=<uLcJkE.-9R?s!m^-7%%cb9'1.0_9Wg.hP^:`NUKn^JsN">VK=FNNVO:W+upDMhOeuE=]<M#ICNE,Ps<Xoc2+f32Y$^PgeU;T\K7d$h0[cpe=2RL]WH0*K0UIJ$1lkGa&Xo`VKr2Z(d8CZpjmahf=EjF&$(.JW-h2m7XZFXCOZdWL3SIO*B9s+;i"/$;\*`s,R(#;S"pZPEfdB7.pM;@T/Kn_s+S7B6paAV%bhf(@fB&;'>?I40J'?0D-4V\mo.kHIJOBLGKD='#dZZ3ppaYIVGP/,)!4s(+QN`Y]@Uc&+([!lEUIh:.<q>]3!&_65&:!N[FU]r"^-'_7)!Q2@PT`~>endstream
endobj
59 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2840
>>
stream
GauHLCN%tK(&dQ-EIh_+n%rQ/()<JjZFfYDC!^]8")WU:)3H/##ruNUUh/qsn$t5"76@qg-UJE`VME(d^A"-8O'MVSbg3XAqY?Rd?@(].FM/kOF@*Qf7rPQV^772T&G_6GS0XW:d/q'mIi_)OYM[WqLpgrRU6+N":F/G,@\*r'E7PDe@h0h;H>u^D/RgX^-gZOU/f$Qaf)1*N)eB.!FC!>jl_<6lV/5BgV%.qGj#MDQm-f&l?f1N$]5Un1;X$<?f1H`=Sa.B^q@d07`!VKHiF#nMg,;eC\44q#PtGV_8>i2DYOLh\F<d7qV06-V(XS+0<OM_3M5I9!^ieELk4PJK.FsZ0GI%$-!^#b/?(-*]ZG=<MHnU?h(S>4(OV>t;-sYPcO%UY>I<k(@2s9],*ln$QZDq)q-c\L!qbHE7YEZbrqk!M+iV(utPT?(lX50Ph</Xb:i91lCaQUg?e>B..6?+$Y`"'+M<*O13rBa\QFWjt:RU]uLf\$"ONP3(F%5)nn,&pJ^Sr&rsKq:5a+7m8i$9g3tI-A^N1qQ-?_aVp&6DW`M'J3bs/&q$4;i3LYGnKD1nO"O8p!]=EUf^8`YIR-15BbbR"tpUijGqLSLmt@h05ul`/7`2dlVY.c*V:.B,#,+5[CKI>>nqXR9<>rhPk0l6S2*s':`5*Bb;gTt]\QOm9Cb!+28=Wpnu#0aEn!9)V8?/(20WE(YUe>-^)4_2^94JPRhl6..s_d1::O9qnN?f%rt\e]<e(%0;UI=;#NY#Y/b5cl,o=RYFsHOJn$r/\ht\@+m7$4aq"%+cZI(FEiR=,GfD1s]5At']:eI9NMb8'RlA?=4U8Uu+>No(QX]^i7aeFThM*onABYGHm;j6OnRYk?jC#4Z?Z_,.";&QCCbZc=9Tmp$VL)Tn>>Ho_)8Jp(I#aTWCCkSF?'^5h<HP)$n#>a"P*G:%Zb6nu(GSrLr?G[4%FP#0j?lMV<S`Yto<@tUpDN(l+eK*XF=d.b4b87m*@ZGDO$@7X.%g`%1b/cRBZi0QOeo4_i?$%J!>'1:khMcH0g:'CkkR(?4UL3s[m:8<4;5n#[Nn0Z"LeCAj;cd1[_@i*=gF8I(QP>&+,2*<dgqp/CCaf^B;**/F.Cm[fMS7P:Rhf:aoR!jL0J;_0NG.D?/<fQ9agdI4+@_N[,5nUtWlEOK=*`0u/4>>_\qq%IZE_2uSABgqk7,ET,ai=SW@\5t%#K?Zf:poE#q4F3`"Y"M,K7pq'hkqo6;o`^KQ'^0p]@-FRbms/,+Gtqh,(Zpc!&hqmaRRu+Af,oj@m$WQaU0EMA[d'gR3p<oth%'JmX"W],(\K*;WYf9f.X2)YsX-8q*F6geo?s"Phh'HS.mb:RGt-*8&W+F$OJsS]KPL^d;sQKd#hG0F6Rqs/.5`!]pEU1B[H0@98joB%Pg"/+-r/I=(_3pC@^BpAl6>kJ7ItC]W-IB-QFd1WE*r"M=)<I"S\S`j[P9D2Vp6.f_H!\CSj74U>\/(nL`;/dnpjgD\:tb(CUb\VhGU%54#dmBOW[!k._4%f[2H//(Q8VgLqFWZ)Mh&ge5a"r(#hqA3Y8i&7@AWDY1)ku9NR1>Qp\?I9Oj@YD*'[1Z;6RR)m8?@lpbi^#0oZ#V_20GNKpT@"r&<STb>;dAT+pjdMiS.unE0-tHc7\8sbB'NkC/9>BX42[7Cg8Ldt@;8ZsXOBX-cY#1q<1Fjd3oWcHpOa1)IOi_nSgq)MC(?P'a3+VDCA;?/9C.;Q![RA=e'NMZLXC61N90Ab[BX6d@*q3^[=q1e)khA52:WJSMc'-_J0=USK%lP1&o2Fs[A?\B\bAQ%0Z9U[U*Mg\:s7]s+4Fu9Tu_eOR-qSA7aG2QraL>NqMiPlNLs:e*5`N4MFDCI;;)WiKF><3LP-:m)22;9)d/8H_'8tu#=o_)DSdJ0@o'Ea4t7C&Cj8C>B0b*l;f+OmHGelQ'.TYiR%p>dAj#PZ^eVrYd++4""]!K"")4WBIO$_<`RP/e,rBIL_//-9H+*^>pfN\eRVBPOb9t*->3:'&al]!@\'&SNT9Vg1TiAS8"R9h*isu]RI[5Qu#udBs1UNAX5rGe%d@Fte2E@E=mBf7Q[4G>eenMsu&%:R?B44a]bZ9^fLWdmP:,XNpKspcr5rmmcR#k^;leKjLs8/T+bGM>&f"/lf@e+-p4nH$p-\'+`7b)jWL7M[-YFYd4DCmT#Cea=fe0Nj#`51)bnS@q""Xe[^%eo&O;5-XZ2YaB/%M!8R0*7J3S8,?Y&5K9EEh).</m\Hh9En=0h2(XY.7B@PEUYY>\E1X;YTgE+jl\54U&;W_)n\'YT5kApQM[qnXWR4KgI6V!ou8T/I'PU<(sG*5L_Jsnqigi^[`?Mgm7r6bY)eX,0^tI+-@QL0duPX2q&]cXrt-<DH)*qE]PkDmnaA0\596hmPGf>$N#pL`L7WH9Im.f^4mit8]MmTZ*=CLl1gF0A\*EG>1`uLJHNJYkL@`7!]9p%ufmC6C""Y4TFW,LR,RZ!)4omV`aMHXrJI_]V%Sia,:MUht1-Qd!F9!XuS\[Y,H/Wt[;p!d[,2*(8`ksS\c-"g:gdP.],R5^%r^[Nn;]KS*6TI,_L*MX;j`?5@-])&ANd<#gI#T<HbQ-LfblZ9E470@o,R5^%r^[NNn,tehK1GN3BK2.W=k6$LPB+1H"TuD**osH]4*X,dnic@CpZb"rRMGibP(Ss#^Gqa9`CNk?7nIeN$.&7\$bmhkj39PZSm8[4\]tQoD0mf4h/rW5BUg?(O(@PN"^sMu&:t_lf6hi&CHfc\/e>c!m41:-(PNuXFq"u")L.cX_o&\o%(D"CqoH1?]hYB0rrK$5f_k~>endstream
endobj
60 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2695
>>
stream
GauHLmr-r?')eE:@^$+Rl,%W:gX6i6+^6d]g_JT2D=2oXnqEBDRuKhIU?'i$fA@NFQCT@B>-)]q=rA$n):!Rbo>m!pr!hK^APMg?%DBI_.?*J&6")N?kiP%A]/fb92Tau9.MA32aYZNr4L8^iV"F+_cR(*sT4pn2R\g\IPbu"g<RDn$rIRtl_2:[rga!2a/BDOgoS]OH#"!'jr'AssjVH))VP]9pC:t69g![8\-Zg;=;[S0I^Zat/.#:bcE+KreXX`R5Me[$mI76)ekiO6Nke'Q3c6\*]#H$Lr=aFk*.2u!i'UAS$?N!P:fkdY[j)R>8AIN>&m`,eg*A/68P9>L)rR/H=V5,M%R/@PIh9F4H8rF*+\?SU;Uj4")bW\p\N2@jq-Q.VX7Tg47`aM/mUr?,Ir\R4\6uqRbL\&FJ;tHVe^W?<:E;LTOB9/ocEd/.'Efh_haHXfA3/nG5MY"#W$="E1!?;7F8&8j]i".7EL-A;g7\bKC%R2V8]/;r^o-/O3_cKC!`e7OBeoW1A_gs9_Au9@C?")>O27*rq-`NEKG)`T"DCs\JUaF(QWhlQC:aJ'+U2WL4#sF%qnZ;1N&l)1;U"<`BI#rkTF93]9UG/4V`!\8$\`C8QLMPAG8hVQ6=]mPT<`Trs+ai/c6ZlJ50PMbS-Ts@@Tl?G#*CjP\V=j:]acF7lrQ]g6kJ%O^>-tS4U&rf1pj_+e;T_"mY[eYMeooJ:kaLoCE8j<J'E^B7[?t\CJ"S5I7D#*q=J.-P#bV+e;T>4TN9P>dP1*M^Ne*JnhnY]@Yn=+l84I;>k=Zq@'!tsFlU50/TtWtc$#CTf&=gbY&ZA+n\PlP:b%OG+`mc:-n;4G-S`YMoCY@@J//cSti*Lrm,i0=jABZJV#`n,k#qT=s<[n3(3?9S`/_s`P^TPNr\kM98%uaP`&LB+R(OkG'TBjoKN.U!]e`baB3/.+8X)$+!T<Rr`r;1S8qF=lh#>UON>mH5``U_`B6@8F$ppD&p_XrKUYoCl0A(c;^hMoMO0aPdJ_."5hqOt]aI!glmMW98K;]$3/Akk[rQGWiSA^?&Zg)YiE(T3=mCHe"#<MAeCdcMCSdUY$NKkUa<&I/ed3Z_8s6b@_>l7E8?a:otm_oPL<<MM9#%Nf)Hjbu(NH.0'2]N=Jm4Z@/Mf]h>uiI"Rt:fn!k@sa$lHrk,+[Z/--.<I2WGFU.qa3Vbm/q.<J+k]o#B0.]Aph+<,>5\V[SGGYtCE$2LgE=]JK\:4J1iO>ERAifd>Q,+)@4#TO`!J,dEZ&)KVA@6=&p'kBVU!=rBJEC<E<KdV2kjI85b.RhH`l_H&mIQVfktEF7]ei'NG)a.4/-)A=i/PSQpho@;$!;TDCOaPA\'l@K]gE(p[MW-je,t8$kAI2+;B@[Hd/L/;s\U=4("=c-1M#%J-]GKDRlKQA$"KZ<&0B&6bgb:hDBFo.nVHE%ddYL(LhRXk41+WD-b>n;%3HT=a"XkZ/Dj,o@>I/hr'@[>19u(K/q)K^!kCH(_J?"#1R9-8n2)73$NBN<)i-9#E(h&FI(Om]"\"p6F7J<1g'$kAS1dE=^%fd$Ho.Z5tLVOnNB(1=m*r'We]F7758$R/CCm!Z(B-uiY'K&:lqfa;6gpkf\Q-ELdjC+.TKJb)Ir1:To[YABUUfgW4ZWEBu*'EeW)/VV+8l&>kT9HBIa7r$.9:VB:Z&mEZGbE!>miD<diXs`<+:r7qpeS-demEofsl5Z3>K]s/\$die.SfH<.K*cX[Fhj6&je6hTfHc';`i^UVDKdsRAqdGaft>4+F]MdQT'G)t\&/4KCd\dFp68E/XL!,u'8>n-/pW?iJ-],k1jK5m@L;`FFUX4n$F`e2Xp,CRk4E"q`V\:+%)mN`Y$b1blW<q&j9'^HWqCkSgU<F\F,CdfW\5bGGhkdgtq!PV4+:4"0?E<R!_Hb94Fp3OXc]9B?A.*!@)`3nk.)13tb&5@LgX,S/bqVjcK%T\]/#=nW6e[Wj%E:)dor9,6k&<8bm1M6h\nN9E55opGr\5;j)Z.l>ard4Uh]#%o+2$X1fBK1EA#J;/,_,WqC%@q)Ri'JUJc.8(i-H\F)R^M7%Q48jVm=C.-]lG0+UE\C'"('n/WnUTm!L*Xb=(L5sGM,:-5kdhHL=Yjtgp4fEb<?([<@`50A/96mG"(QaO8n]-j)Iof"c$:OKhF,"-pupcEe/0p@`DS.hSm<K[s!lNU$1h<_5bU:Lcsdq^!HY8F<"ij7F!Vn=.KL`5'Lu&;sX`[k8"XW;6qrt:*>_@4S0ABau@sZ$.*-.-'tbt7jgM@Q23rAW/HCDYMmAO)@p+1MMin,nBCB7$HWjbBQ.gq^S@;YH`sW9h)?-l"%G9b<$-UoL+BgPcrC[-j&)PZHPP#S*Bq)9+MX.]rLiaAc,p7<OaZYd`=N@%eirj,iD,G,@95&p`]b&`p)3gN-6;5cY@M<J7//WS'Y=3/[<r]I(iEoqdbMj^kTc'PRI84`-+:!Zi8(8k^oe**3U>J>)OHe;d4fF*347-@iS^?\i6(_*F<4;9VOfmXBf%F20A,165&pU[GuMF\*oleH\"((J<>L)j&X9tY#1&4X#PU7NR[uWDoof=%Wr%-jkB5$u+%Z+@Ns#stK)H,PmdQu!<-XY!ikQB7:h]0c%f4tKf!4f>_K&i?/UD3i1E>r]]2hHl]mLkrFt[j%VB=.Jm!g>Wd%C~>endstream
endobj
61 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 3062
>>
stream
Gb"/'>BAT.)1C,?p`@pccKrul?de1+lrY:+dA45$l#]BJ=;"j^i=]pXPdL8Z4Wcq0WJb=Hn`6\>ACnhQq!R;b0H_He!rH-gLgFB8bO^79O=k;U@P=V%+6h&3ai>&JO-6`'aii_g:C;KI@2:6_rpM4@6FS<o,r&t&839G,h#=FL%k$Cg)><",@Q_qoK-Ku0o&B2D`5b20h3K,g7]5U(3F2(:m(6kZ/N0o4[r(BW<L@A4q!3FVq0t^q9\dLqmUU*48`-qM3>c=6d,iSqq$e:MhSk\"na,#I<9.7VYB='lXsI#(7Xg8fr^JiP4&G1mA[R,$/@N,SXt;1V%ukt_:Z:/ToKU;q;A_#E^I)J.h5O1QOJ</QllZ_"'R:!F`rUH_(++%k+?r%YSCS]9*5X.kikUlH/G,mUQ6^X"BRA/b<H?Pu8bAee<J)RIOqd"8s2I-)H.Pt]#:V]$U9/[FPG7JVkL!MF'fb?K#O41'HP&Ar+nakE#/A7L&&c>fHU/VS=o'P",+i<MW#.n+@3LFKFh:qsJXuC]hl4%`HdQd<Vr>emr<p1t6O0Dg03305/64O<'!BY6*EVfO:R9#\8mtea<AH]Pq,]4/p*m_^djSK*EH8<T"uc1dLC^;&Z1@MIJe-NnK:uJV!r]?@UbIu*iinV`D`GMa)I0p;NGoLo,Pr@sp^H3@ikE5/p7`r%%;hq8alSa%8!^'lKl`UQ??W&E8Cdmtp.;>1mX,`r0Qr/1U:sPb8i4e$[VKDtUIlsn%=2V:<,6eBPK$r&M?C(M2HukQQtr]@I;>sW#%?fYG+\_af63nc7J?F7,KlcZ]opC19/N)[EAkI2ANt:"Y(`QdVf,d%MQ!Y$"EVWdGAW6Ji+7loKTG!g3$>O+n1=taZBrhk/%-:m$+j`NFk=6*?-bD`]'G"8f;7=I9dS)s3nnAt_dXp<5p^P!464u(C<.fpTUId5i<&%=.JqYJH4+4.1>ZJhp`)F>FpsM)XKI*XE>W2a05j_NGa0#s`QBNC"uf;/W%+rgOEuURBdYF]Y:Ba*KC%Jd\5E67HG)ga[E+?mWqB\?rB9=6f2lLiSaO32k+)>"K3I*Qb,.Gsgal!hW-GO]JYtrGSJ'80GI#_(jnd7tb8C+Ys(#+T(oh(u\<JgBCfKFeru>Pp$.FM1N<M-=AYXd<@=j,ukL"qo?5ODcOQ&@@Ii7`1@"\ZmbQ.&^^-%ISB?o^f"qe5ofT%6(GA9)0)hMm2JcTji8cE1(:N'f[A(0h&2FHqr,5/%R^Jn.6L]+Npcn+Lf=k:#a*g_VAR@iF2=@fp]=D(T%YR?(u\bf@^o)q`%2#YhkVGUR`VK#^f/%SK[M4JNaY<+A^EiS&.\,18e_Q3`q,u\qO7"lj00:N9Ijdd8FkSdf!C&Q;5DkD5MDtSd%EBTiB`*@_J7^bj9PVe%;E8UY)Y+(e2[q>l1+`_mc_k6Gu#Q4Vn';lo5MY2;9IcHpZ5\j*I('!-BJ)"I^><_]IM09C".:HS\F6;,,#I0\*^B]:/d68%jE\?_/R:4+W=d>ph@4!A7k+8Xh_u92Uk,6M<#O?BgcYic#q%7nJC9&.qaC^u2@\_!..FETKX$V,PLLJ]'P9IfkJJ0?0iu].g#93Og7%T;h.f;e-i_uH(#Ei5)Hr?a[,psg#f!R%L1r(-/+R1d1FJgX'Bqt)QN_d@`:E0qu11h*669ZtH8)2ar4#b+!LUe2V^&a.C,GAG)P?^a'5!Xsu_=VQ+:"Q[bS?^NS9#2$W=OS\\!=^$/<`,1/9=NL[oNTF@ionNrnod8Of`MAJ?C`CC-t1@V4u-@"!:FU+*fI^t:8&]fBKfMSm@glJ$F=%tS/30eEW%R6'Cj5%Kn"LNM*N.>:^Oc83"$ef38EQ,`i<#,O?lmlQJ^H3Sc.5i]ci+h#EYZ2AKr5q=)ngD;RS$EU_2+W*?R>ScL;)!P%1s<meU`Q<+WCi"=@P<8&\&&E-2.IED.Bb8CAKk8+39OeR/OuR_$Q+!O5d+6_-*uMTXICrG'jn(EGZrJik2V!n[V_:,\47BHCZ&'Jo*a<PQ+3h5BNm,QjHd-W!jBp=$n%BJWXl%h6b:0"%O#F8;Cn6I:^*guu7?=O)(FCM]@^T&!g0!_KZISAr&,5Kl!IG@K`7?r/!!.1-IhP8Mg#3!Jp&S(HQH[a?3\SCX^rY]HQp1id-$SS3$AYtDoi")-6]g^/ZpWWtWX>heG,652SSDK&5gHc]>h$C;-N6=h=RA4rE0Z,S;WXXL^pdHDQa,IbfP0%Kho=$t)46s%MO+C+C>&j<beXfbMCc.\>H@7k@FSMZ'eB<Ql:biu1m@`E.]F8s./\IGY_MnMp:IX0O1M2=k5.HblJ"AmWc5LKm4F[0`n*&Z)G0Y+tb$dHbM]cbW&F2mFi8WML%(J'V.ci5X\^0Go97IV%&#?(8Sm_H$@<HrIO+3TZuNP:_BLd*CN0T:uT83*pXY,(5oD4Z>B2`'/koue:&"*[i<kAucjAGBNgH"=`=hg+]K0hJ^e>n\"mUt3,t`Dmt9L0DjgXuO?+6nG`$ZX?Pqa8lhJ26^8,%X[r[PtXR"=`hP12Sa(P3b)PDG+X6G*,n,m]sRlCs7L@aD:S_j0]S<D57Y2so1b"r)Td;QS+5IflUaY"2^Dho"Z)dM,>'r[FK9^a?6":1]E\u'@nd^G9PPMj>9-d&R[$2mFml`2FR70O8."(,X8AJ?TlCR!>mmr<&g)gZG$!Z.0*=+'2tCY"G%%*5cqUVWG*RFITj-8LK44SK5Rhg_8U35MQ4N;e!PH#VqoKWD'lK*7\69d01(#W6NpgshLI>aE8+/KE:j!&3`Eg!pkJ+uEViQ4U];[g)ZTPjd"gD=rAGNji._01^3XCX.jQ=b0'-"hBCUbXa4Zr$-j40K;KHqDGf=7A,^C[k$Y5*htOkPt+Y#qbW`4*@4=ClbOgSb2qeDs^EGF>oN/bS%:_5beb]/M9J36\69'+]@(HJu0g>KI\2e4W!ORt3f=;"8Q+OUiWcni.!OomImeSGdd3))uO(@N]$rn-p)X+(O/k/6[FU76bec+2F_2bOFsDe+>XQ9n+saB)-P&Vj%,^@IIE;~>endstream
endobj
62 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2967
>>
stream
GauHLBoh&h(&Ye\iaK*L=2kZfq_/QaOs:9RSCi]W#Qj@Z*jTFU'cnSX\Z>8(:VCXPHY=\ZMBuq+b9?ageQ(/laMhN4r6-[c(K^7qPt.EA='P5^-`!dbl/gIKLGL:e,!QIW8]/K+147)j&k;N>f4RiH[q@Qe+XN7H'h(u7r`@O[ZXLZQpL(sV=O%5d/9Xs4_I9^j`<D=V*C&Hk8XT`\\uOubH$S&#NU5k'SNCr\`sI%ZqJZ#k5JHGRp;3l-Q*jXQ4g.;"e4Ms%X7p`//I+,cKk#/^PhRB]i0m3o2g$b-RWL/Sq&R3G1Yp.G8@cDdM\RGr@bl.t[7-nQU4MX?1"%#,r`SS5q8)(Q[qP,QGO/5eL6r$$g[i*,7ULQ2Yt%QNpedF7lOWu_^/epPO0!/Y4YsFfa<@sfA(-WTjd[cV:"+=9m3V.gVRTW;8YRh.eXb@Z<4S,:[$I8+kRH@*\hd!$%<W;-<Y@?cFK3^RZ&["F05C&LbIWlCK1B8SNDN?/3230Kl9eKc8UB:dAV#OIjgJl--&]Onl,LDc_u\IHFMuF%Zj3/\7Q=`<GtIq,+Vl\h\8:@u^n9i2l`o0P5pfT18DTP$Y3[><<^H"KKl7]H7`KqC\Z@]pV8-;t6.iV_.bs9jdPMm2>Z&nK)d1YP8/L,4%/ah!Aik-*'SYgk:"-60p83,0PH>HDWTkU*>G5tWI<e"f3+'Z]'%=`Sh>Gd2C!HPcppDP-*RJ/2I;s`7FN).f6FV"1:1G%ff$6I.K(S7Nb+b/nH;hsldp_cdq#A-JS+='EOg\!5!UioBN]LSlT]JJHaN6]FhPj40,JpV#HUJLPh2"r/(i-gOfYXJb-$HA^:bE4b6.IUgMf,uZ/OQq-2mR60VCQqeYmb!i*C9e?B$n.*$sh/?bF>6P$#*dcM[gpj.;eLkTV?6D<%dfl]e,^XRo\BF)c`qb7j@u[.m6RDg`^i@3qR:'#K4#k$GB:tm,eI<5okNs&05cdlr>`+ea\:9pL8Niplf+7HbA`snVNNI]P"FbnX3%=;56]aJcRJsd/fSmm?'?BdGkeZ$t2T:<o."ZFSiN2GC'au:pg;R/PEhdW*JhhjV]U7]#*f-CJ.YV*YN'b(SYa2,rX<Y'3$BNQ]:E;1D$.S!36BCq6hqHSmp>l:()qf][m<_js':8QSu_]s/g`Q-;:9Q,<epE#$$;!]=m3pdVMot3"29;rq,j\,bld]#O4ms33H%PQA0t2$CLZU'JT:2L4`Vlf(_L)gMbDCZ\BbQUSY-P+b*D<#pL'Wgh,'^#siP3ZTcGpI7S7l8G/rbd5/G$d5-H#Ullhhn,4WcSn6YU:iQs>A6H!.5]aoXF2=F90]+H(HM\!I_i_RG8F<>O]K>d4V#/''BfdC7LE<h@A%o\,9Qg_XZe?m@L)kM1>@k^6EVJ_B)49RD^PZcTPlM&]eDL&-qRa`GTc6l&P'6nEM1P6lO;,[p=(/.<':6q!`(FQr-m3N0ZHs%%d#Lb%C,;E+B9L>39'^<*^0r51HYe->@?L<"o3@t;/!)W^!X/WddZ6;#PHk)$&!=KnU/_iNU;Pkp5_tR[)6YXA9-7]i9ZGNRLa]GR7C</J7?Rc-)3erlL=]-_h(V9#[!jT!cphloP9IDPOH=$Gp'Ga&GSBO"'coAum=`UB,)i%:\q:eVCDTtB-7M]9$J]F2e/Sm4*Ena"YO"nSODZAus%3@o(0RDCgoA)+2HmOJHj)'Ekg=e6kBke!RtbXl<8GsW.R.tF&A(jU9>M<DIT2k*=)?+C)N2$ibnn)!a1n$)%-"[8d,u>3Qn?=d%\6kZ'MTneoS]rBRgU!$Z=)=WhO'CkJ$L.L9i_pJ0=Q@fRC)_@*&2pSFjDPU%)#?M"s<KT=oj36d>nf$HNcY75<6eFY.dEr4LB\="Zr\D2KXrq[8MjhG_X*#h)QLPKo>/'gu)Ms'\0?EpDLY4G\_sd0K9Fmf=2\61HYnd3A5$[&X7?DE2&^?&hhNk"iQrWWZZ]!SKTFjG^hsX:*4J`+'>Q2>*D%o6;T+7DBHID_Q4J#J(HTf$rt"(D3(1E14^Zl#A/&5M2rK;;\rs%I:)?bcJ%c=?o:s1pmLmAU0Uk2>N#e27\m^Kfll2eWEWskc*TGa#7F:77L4B4a5XjrL8BVB(WO;\E0cM(gbN;OS..&_@Um69[Xoaq[G#_V@5bV/K9A`MEN`n'i";%.E@o?cc%j]i]S,*Dcsj69[Si^j,(]2c&3u(-2hD']$aHH&oit&).#@pClP/,-o,mL8r5XFirrD3o9]tWsj#jVGc6N52cGS!+8">>F`ViES,PeG4d*h:'@HV[J3%4!&2';Cui(b7k=^"uuHnVTB3E;H5B#!W4Sp4`O%o;N[L(*Ml(IS;,k9D?)HJXHYbO>5%.`mU'@e=c>O].en%R0m\TN(A&SdMo67DjiJbGJVXdn`Gs?GP&q5G^a#C[_^l&P[0,s*XH+CMV#p]+ZE6kAY;9?GU<mXXYSTS3=d_V&-=ufYqm+kHUoq\<eq`R@)3$T;Bac,*oG[_&f.HNK\j'5\N1F?;4sk>c^W$6AP(*71f<r`:k&9-"'VUJ!C6.m""6ebc?b4i"!Gdbmphi=8>!j^aRj6R+"9KE6HHe+Si9PdpoqPJbH;$*!kHli>m=YF/]s^(9W$LS):&-BuBSbr@ISKnm;=oj`>7/-`6Cr5<o/hg],Adm?I@V"$BduO@r_!UuspE^4_nU)lPiT9IP"![k?Y6MUBVQ7ti)qK&f\Ur7G5M?92E13-!g9;498tS_WaAk`;pPri`L,*gQ57q]]$0LYX8r[>c^k^-`clr<2+mUb7aI0FsN)kA1i#H*h=D*,5rW$B'"r4nrp7<2Dc6OpZ<GeH;'\Q"cQY0fK?pkiHT8R3V>PfRRVZhMo]]!YgEA[Q6"JSj0o0A?iQ'lQd,MIjM@Z+bi0[4LC_f.(761`:h$IIt60tDW#o%K0G`I6>uD]D\_'OZh_9tUU0t$-\=/<~>endstream
endobj
63 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2940
>>
stream
Gb!#\CN%tK(&dQ-EFB]_Z]Jia7<3sRa<knrmAB8o?*je5AOMP(-5<H'%';"o^?<f2A]O<fgN9\lCdfU^m_.dIc5?iIj)8=T(OMnFDWp@HTHL&"%0a!Qe'/EqlK7I3R?p?6R)e9!EU"o35$)/2-hR-tSp:V_cPfDb8s>A1PU)[q?VNbUoc'cQ#!:uGG$Z0L.mG73mPddd>R3l;GsTe=AN.isAl"c>lbcK!V4lL8iR)MP8h'7rJ#;O]LOPW#$eMMDNNNV7hMD$(/,bEEhU9Y-Cs[JE&'i.hD_k=SD_8Y9RmO-0F<PDp/T1NYm\Dm@iNC@E!R&"*Zt?m-ZS^Prni_I+p\M#l-FT)SGkUWf!-WU5j\tHba9$u7KL)mF/g4^EO;Fa%''Bep_2lQX%u<StjY.0\cB^/TX>31iF/7"'UM</o[NhL,j>Mj;gDS]Q,?6%)WoY#2&#q4W/?<B`WDuo3h+@"]CH@?mfM,%47b0Ha,ukD9TKSqi_XaftZP*e%Uh+$]XC;'O6Gm9e&8i@`;BOU^9@CG\X%VfnQ?6r.Watp\HO)dMB]Va?ZU`-`1I)/O(`Y2bK-4HJ"B*f<'N!X2`&dsobJ1DRE]2*5(NldT-90g=SaJmOT4fUkh5LXUDFO@Q$+f'&l`.*<6rNB)6:s1%am:;O,S*B4f2@__b#^5ePY36Z*GqfGdd?.5kehas#k,(VB0g=\]VB<k'G-RLj3VNCYQ/QHac>'a'ghA,T.St%p(DN@!Oj]`o]P/U5ui-'3!"#/C:OT;$TsMq8No:iI7-r2DCX:3p5HmAB++7ccq@NO=JB23j&t$4`,rm$Bt^4L?+K'^lnKaTnuppQ%A==o*1&(9,;MJ%'o.F[WqD5"XkAi>8hQ2AW\RSja=g"RZ-egpW6Z&J"W,@>0cJ4Lm2r3Ige$#h?sQG$:6RT9.nlj/4k^t/o95ZDk4Q/+hufMd[MX5J%L/iF&1'dG_N:7H/.C-LgF6<MR_dJ9cMfetXM:2RKC)'Z3AK6Rg/ND<$ti[DlWU$eZsK8dYR<k$>:NjY*WUHX%shAq.g%H]#k^q:3R8)Qq2RDg$A6"&r3c%!#-o51/I!FI^^L%0pJbWKn^psMp-Eo@Yo>GcgK\#S6RR.fP_['^T.Bh20rG)E<+s*fO?/k4fC?*-P&>G*KD')FNZ$!&qsJlfnujs:?sKSY/T&X*,l[tn3[KP*)_-FiCbb(n(??>-_nqoYV5n6HOjtZc6EW&-4CD'tSs\%1(.onZp^ab!KG[F(*\dN#$Q*]lmEYO=D`bQ;g`NCf8I#-r&%L1-0)EDkX(59_JAO;R&-RU;MZt`LQ`&n^EC1[u&qsXOO/7sY31uRcXPq=Fjq#tlqlVD!F8BuiKP=1Q(_!5A0$=,<b<cI7a5IlENMRgGd3V!7qrXA(hl_10fLcM.No"^h'P$B)e;s3cCF;D&@B)in\9aV)dD0mmh(,]s4J=9AreUU3j6,eS]2"7&HG*t+n]?Z]Z)6k&s5!p/HG\O.0Db4$?Lm-=UcqH:N3NQ\@`*uh%Yn*<3d]bl`cfSnV.M?q?.9c2L7,\-Jn_5Jg$E]"3X6a5?\K0*ri[7$1B0Ji;+`pQ.L]TV]q$^`*:7D&Nj/aiJ'e3iE^XX4Kp!Yi]MFEF57R-#/aEk_A74i`1_SQh(;0q\EekZ3WTB\L4%(IH?:.(bUf$o!%[k\4=lB_9,gG5>V$.bW9Zj_+;,7a07DT^;2HS0Bn-dsmVSeXNdV7c^)R#HtQ%[pAn/JGc):N]/5hM/a_.o+Qk_">MC_^WB26dPKp@<i8/Ku&!_fC/%Cmq8\^fhH@ZtU'#Y3V4mCpkfn/hn0eM+V1Z'qA0U3@e4,nUO'A.qus0*T14-C*%$DJP.7Zk_&s.@[`C$$S`$S5o5BEc3GJu78n.;cICI]$ho=<ljuuBf7q*CA<72L('MY=XSYT4SBO0VL:NV\&0WkbZ;1k[SmtZbldM$/<cp;5@u5+:UMU)p&-<K!OIh&,`D,oEa<mn3\T5J/L!^9[E0rM9Q@P$]"redg6)_.BEnH?)!_N%T8^'@l2J\P7POdc[M8K0Fd1?Ig>r%5Dl40[E:Lm1?>40GH6J7*uS:r\^RB<TPlY5<mq@W3Vb9L*7J9:QpU'q#R(u(HBBK)FB)X7;d0(hu62Q#VOn;iX.Af*lR>(/;625NE+r,RZ[Ek6Q71$Hg<n\Dq8fDcaZ-)C$2M1)Q>F?`"":l[Xj#@/Y!VeJ?ce))XsYC;*L+6NQ(T_Rk&L<k<'_1uau#ec"onB8m9qBWQ1lVljs$7JR!*B;9AG(3:P(Bquj>IkC5#99bjW,ntg.^U>A^6"B29;G)!R,=)%86oc`=c=^fYS7_%=IPNd.Yh3uQ^R`WfYGr6.k$ngm0a'tcP4pUDf]`O4.:dREU%*Fs(D#@%Zq,)G5qPgP@9WJJX:cH[pAp#a-Ge^Vd1%`6p/]J`t!6i=UK[N8kW*Kk4s+Yd=[^3g-@>SbBfLVmTd#6g[^0F-F,2G5-uOV6f*"[BX*AgE+F<U%d#C\72i;JX)?Z/Z:bt-j&<^oR&8Xn`uRHc[+<N\E\SZHLCV?[9]IEoXr-M]^+G!WXYUDCS=_OBJV-Z!VEH?WJ/R`gH8tA-E[.0fAUI;4Lu'3!m5$PL!$LV_X[DI-H:I<\M*J5U!BY;C6<dW1`=p#M?Wjmm>TkftA7#O\paa_Qo;P(F2;<)9h,b&9X@ZFg?%4\C>s';5AaE=9TPt(dp-mRaOa@!nKb(%$cC#-aDsnq`!::[N_,M_Yg/>"@=R-`:Yg88"[Z>Keh7"hiV;+V<>jZRRN^e"VD?t(^1:0b4Igq//iIYYfi81m*DN3!C!R&-igo\\tE"K;7C\0el'r.UF)@((CF#FNFJH[ff+<Qi9B5nXTMt/EXP3=DoBAdIBM]Kob4MnFcVqn*NRf<eIIU_bQJOT`+q?f'J5"2720;d,ZE%FUorrkSr8Rq~>endstream
endobj
64 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2924
>>
stream
GauHNCN%tK(&dQ-EIg0QG9Ja^^6t]DS0ub9h.1#g.$-)lC*YO-8;0E6EIWD_*Bk`oD:3F%$U7$acHNtCmX%ET>l4m!5?ef7]V=S-"UU6m(*ir/TW<RhS#_`k-ViZV?5eoh"L/oCpl)jF#jKrb-Vd4EPENe5im=GXKjeG^$Mnkm/Jqt+<_U-eS3Wm4Rue;*MhNbhK'FXX&=lX0_1\uBFEUMt<q9EOoY/NhqWpX*$2=Ado_.16l\-qLD,mW7k8@QiZFJGqre[eld+-Idcq"uF_?GR.#HW=)E-bNLRArp.R4Qhq]_W#lW;;gcQEK@+E!ESKRQ^%ge)@%8laRPFl^%MmQ\rHF@.6YdgQ.A"MM6Qr(i8/f0ENjJ@k>^k@kS8=48?<"n@Hs'H6csSf+X,3))/)AMEWo';/9/ioPppRP?4SE@XX#WPe%n,7k)J)^L]#G0uhZ4(*Scl,3JO"BA.*5X^k"['0c_JL/:i2%%q8V5j1q9)GJCK9#GXWj-5829+CbM#WGI_(oo?p3?f"YNZQo*f@tXc[d\"C?H`1gN.'p_N.=ltJ5I3cX9bGNU.QKn"Va:`F+1&&/Ufm'bpoh@`mn>3g)D$6B7h!lbN)4V1gsHhPOKS;0!CDGhY#g0p\sb3h7HA;)MoMo7'EV]L6+?oga_#q!/Dej;,bkVi-M`JO"P(@[)Ua'(<%la+'%u3Q?bB`?/D[H<DdT<?T>*-SX2uU!.cDA7b(sM?']PpF8/baN`!)()Z,Qhm*E%<eZtL1'teg_J#Aje<%;%'laG#<Z<XE?6gs;4CP&^TGr]igf:0@_JJ$#iC>4hh_TdfO%TCFK3ELL"W7n1R2U&It9e05fBi2s+nEYF]qi&>]=0q2F+5;k.&79$"/:AFnR@D-]AfpK%#$hXhI+bY](sD]"@MU6G,ul6_3ecR"d[O=FaNG?U;rIj4WDH5jONb"V.gq+re;BrclpAMdqZa<";'n6AVe/)VHaHdR/^'[ARRQCS"&a%!;j#rc9fiLl*:TF@KOL.Z!E<41X_WC%o/Ceue`XCA*J,oQ(e@B(GWX/bcd`k2J.Vt#FQe^c90?lI^F\s<QHe_2+R#]*!4HEdGi<j_6a+cOL]HU4F^D*1]X>bFoBT2e(gEuJb7t^4`\a$kRWRBp+lSC)%;LMDUfGuF2-j^l6WYD3-/N2'7`e,``0O34!:"SXH.;um<lU)kbTd&tKIa+o*+n\?2=_ZoTtYAHng.>an.IVdCh_f9Bm\aREi6eKAg2CO>L><KL8GA%6<IFBeW+Jtn6pPL##a_UeW:]CYg]4c:RLqsrk:K=iO88fD'BBQEDA#YTP/'-&]HmMe%Ru:q=1%1LU?X,-l]`U&k.Bt$qm[5#"YC7K/_QrER/dRLGppCFl"6,GVO>5mjUdF*_Zpl]4j`u71]h7C#NnPQZ*megH"$`.*"N6+(so4%Gg2"":56hU"r!OpDspd]4;4!dai@IUAl+E?PnRV4=\NY[Sl/3^slK"0m(>:&D8OS!!b'i+pK2E_6\3M1rk5pRl+D+KXJ$`%_XfMeQ"\qCG()4mCU#h1ZmErY]c$bOZ$D]s-r14.k8f,P[#"qA<97*J`[j_)W&8E?R$!081_hL49rUN,q@Hc'QtiL)7\%>*s`X)[6AQl)1C2`QQ4;rY9e6paLnAh=Wlt9*fXiX^VahV#4W?:N81Z&rNo34-K_JmfBH+^KN/^5$Ibk=?s7I>\VZf&k_Ca,:]o8BKn."&r5>pL],+#gh]>c#MFZ2S51XT:R^=S\`%],d%u(:;kX=LN0h$q?38R4\`q;#9$%0Qd0(Jkd5FR9ur<]h.oI7+Ccokg'/"SFf5c&[:NM7dEs!_3)i$l"jE:#4K/:6(*&481dNV<\<e*mZ;@(&9`.=@!Zq+n7<nJ_RVFNk;U:J?f*;0)TPBLoAEU@/C1j:ha6Z*g3"g_)f`-h7mYTqo2]qC@CWkj7ft!qis;,eYXrOZp#Rcji^4WQ"ps4Bhf3UB"KV_Z9Cc1bY`qZbeF_iA:aGi7g6g(e)^WMtb7T1s1`j1Hb%(<p3i$/s#.3.E;VG\jCt-ESTn4E^&D*mdD,J*:kU:=:mcg:]jm`s..9A!F&uPTSBVZ7>#DaT.;O(/!Q!?6G^GqL[(8#QJS>7V;#a#H>/)U%/",U<@JV]:T;0fpetpH6OQTc;)MHa!I/t_s..\J7JmHLLa9:A,T'I4*>X173sQb<U?gA#]:-5X2"9TO7"hOeZ1%O"L+Z0_m=Fe"hJbP:T?r01l)1m"`>4hoUKXn=ia:J2UKKJ5rSXcBqbp4d:G11X2K^lIK<J#K?p`TSlb?2GD+2MpY_0jqP@tYH.kKDL('GR?Wu-f*N@p[KEd(W[]4:'u?r.V-Ks6c?(B%Do>7>M3K$ff$XG@roW52,D0H!lC'c'kVgc!2Z#(-p>^C7%;+6mTlaF@n6q-24,LUL7i8&NQLh38hZLd0u1/ftp6."92NOoF9.7.@EF$qHB7[DI<@dUb[Lh=dJd<!$+fl'k1j$)6'`p1OCFkRNdO_rk['Xt7C;gi7H_2NGc*0jRr@nGbQrT$W*)l(`5=6oLM$0b1?,(3bus1i%l5G+5MQZWu`:o9fn2=HS%VD?VpZFtq]F>@Gol&"iW'Bo,5/?I8"cIZJ6tqWZhT`<Sm3T5YBkSrpLS0\h)*geK<7MY'hAS<XbInQsoRM[.F+\aE:dkDKL9/cLWZ106Q+5+hAs8N?JRjXb.!Xm2AqRH!g6S]a]LEPKDRL5g@^N4..m3;eRFp0Z).,Elr&"5G\>:,UI#i-?Fu:LBkeh)2d17bqW85Oi<pj7QL?I!=,S_c)&Yc?E2-'i+q^:O=R_#--9^[I_j4F[]*F;buMeU$c)Jnb1JRn#:OMW53HK+7(Z\q$*b3fFJ4%g(Vpu/abP<7ft@02]M2ZlM"NUpH',g7Rd0hf+-N<'@=jN!V#!oU&~>endstream
endobj
65 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2374
>>
stream
GauHNgN)%,&:O:SlpEOn>DWR"HTHRGS%?)Q[#*>tA4A4+"\EBQ;$e_4rk8bjUh!\oj:omM&og0U&,(U]fL72"r'S`D=TS$j'X"Sf:^5APd(g#sqA+OM?Mo0/-%<q`!5'S58XSLU`8VnmpHMr.+l$@f&-`]$$jm9X`'!.#F3t>RE=PT7>B*t7dtf:-"g,"jhuJIWWB['CU5ZkjV?MobkN`kt'b1(=Aff/u'E]YFhr+>5,:p2(f2XCp,r9dOnpIL6\qK>*0`>/WRahStiduVrHVcm\83^'b-L)4C`cLYW?[W/$7D4E!Nf3]MO`@V,RbcU;d_8PMGU1/f[A*]Z9*$TtS,<a*gWb`a6tkJZ0OnE-ZS4Yf`:b!!;aTDt?3G]Y;1bC-:`L7Tq"fRZ&_;3HIDiXVp!2kXJGBu>4:`"moua\d`/(3mjG4$7FEjI4'8XD(]RdJh1Jp&,/PsiUU>-$qG_%?r<<70O=GU.q7fP:Xh5+L;P+M0_n?_%uZc[ME`c*M&?=o@qa$or(An#`H5sRS'(.t_X)7C+[/t<IoF+Oc&gebfX*7eeN=`"lB;Vd15_#dt#/"nn3L$lHbGU!RfKSLeNS\dmJ4$s%obD"AniT2$drf7&e_3f(7pqXl6eYXa>]fgo</,oME.%rB=BLM;HU^Rn"#>H(^%(DcJ_hW,gZpVcj]R0"+-jj1L-qP)Bku#(-Bg?AP%B79,.LqG5ml!KiZ7<74k++SoKg?FFY`+;Ki\@P\nr)Dsb'dMhe1EG\UeOPr(eqR;#H.lGDLR@"]]&?ifc2he%j&a?H^`NOmBn=j(>GqRm4JEeV0XUnf&FtQ_$cP_07d>qk@bisV9KAVRL3@(jNtMX%!T![ToeOLIs@99>h$EKjjM6:oGT#^r)1_3TgrJL7k9u8-nuCo-e5)1oQi895Or"uY:J//du,@Bd\qqlN=;gO]/4;\E(T<3Qf7;Z=LX'WbOo&_Xh;7!/6DW_D$k?u<P9HfQ59b8BC636-9u=nCik!OF80U[Bc_]*;^[KM7,4iQGEFBfBp&"a2,ZMYVl8nI2B+B&G!WN4qO2'NHoqA8;iKsQQeusmfp@=*h4s;#MHjZTA$2.H&7!_hO?(H()jN8IZl1RX'"J-6?m#_s#9$scD2")F"6COLaH6)2M'N`^(n>;n<"S`5fAp2,NZ17PmE`qaPQVb6+.e3N3\3uiMriT>N]&4)<0RR1M]F#;K1N^PELXL+)EqU5(ilTCUa(.!'&k#I]l,jJD"Qo8)^t'U=0p(9>T4b[Y`TgDM'&8o&1::<M8t'+lo,k,DP0<O-8[^p,#4dbI2k+P"=WO7_gJCH5do\6EqjloUV[>k53WT2KG0koFS7g/&8m$fTTBX.fm%IhUpJaZZTWA[o(p/\ied<dA0#:cMA)L&*b4b(&LgJ:68nOiiS)LFMA)ckM'G#M*)8!.Z\cR+g)9GMr&?SQSD\dY*o"ms(u,+ZF7M,r"E\?9)sIJ(Bm08<jPXLf`np36D4/3D$l2^<B]8co3SfmTg6P,F[_2lmd*7;NZN:MLqZ\.R`WR')FpoJ(Z#c?P#?hs1&3VXWoJfM@9'ZFY-3gk\YH-C,i;[\pL?hm\CkTVeL0/Zqj?d<aaHp.tW\L?CXn7ViH8IguCpMZ`E7,_7[Q2dDT3iUCPoi2p+%1lF,C_1[YJ*C`V2!DMdhhE![6$.2qKXT94V>8No_=(o2LQ&5V+k7OLL\tZ?i"5;CFZUa?E`\[P:Ur'G23JR-HT;]A><?<9$W.\<^8"13mN7[]b]Enr1PTt9dqmYl`NUU4Eu@Zf-'L->hd;,jJ<=l[8@Ih%@(gs]c9Bl(FG793q%8h6JDS#2M/:fn/KhRd&e"__9n'J;05k!+DL]Waj\uK[WECe$(mpj\.MkBeR,'E3:-1u5#BuQJZT66qM`mdRo:odmBm49cl^`aaVb14]B83u^PDTSB0i*1:?gjaA,[dDPq:8QRKL(e_-fAi5<mB/]DV"L(UN<[&`BTZ$H<3qHI=EmF=H88g@)>'a8D0!A1lrM.#KbN;4[U2;Z0=gV8B;!T_i=(;rl1i1ptQcNn<J3V"q<J2:qSAS"/*dc0-!(&hWB1dA3C7H&a_V\,@5/H%d,dkIE?2Aot7h@qB>pV?d%RZT_t>'T#Dhd2.8/.EsT@c-=e2:4O"Ah/qhi?Ir)38X<GIq;b;lj[s`\].?h#:Mj%B.PVf[.&shn_h?-i'oJLEV]Ic5jV$0Fl:`t:--Cbm/M8!o;=E-!D=VDF&:9M#L,0-o;tP$Y#T:/D`L4!FSt=ldPLE(3bp.gXB"/rL0,`IMpUd1,>f"6lb]Yd)P.LP*!+sc8?8ml4?]oPUADI7=bqSV[5<9AN1_-#q2T'$[c1&%MRl"U1@1t9m"&tZ%mf~>endstream
endobj
66 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2485
>>
stream
Gb"/'9on$u'"uVp-k)&&%O;NK74Q(oAp6%cP;mO@fu!l4Bot!(%`t$Ka\e:0T3'ho7?-EFAfV"7`.fk#CfY\lWd:k;!VuL0f`1Q3kb%TkEu.Xadf"oPfSf"nHhun(lGJmR77k"Haii\n:KI6qL2!1):Tpq6KFV&m,r)5f82V\bB"q@<m]&45@LXlkH?3C4XHn<)?JHJmHs?qJDu"sWhip!cd="`qgM4J:CY@/%-MQ^I>c&51Msolt^S)_rm_YOCZ8#oc[uI>HVDKsjr]T(e`=D;'iaHou\@7<qaL@c?V4(ZSL.j3Lq)*'gK-$jQ;XU^2@Lg_ofVnLcD;o8E2"EeZM='u5hhnP30V'co&\nmWQTh63L+G%25o:k?i"@fb!I7N\-Lp@-5!DCDCCPqaCs#$`fTaV^O'Z`qb=C6-P!i61dNj=q"!NNE\_8rQ>H3F$_GIr[buPTZFLl:seF"U4b-\fV2D&c<#(qq6BPY"<Mr7/890XJ,n5gKV+;WhF(W8V$/jB\OPmoGN[-C#_@3LFK'U`iU>1'_=U[5Jc[G>2^p`EHc@:l^C1,#K?Na#@=G(gP$H).htA47$8^!n!tCOt9'.$35m1`Wr=L:CidO[,u#,%3>?R+#4pK]fD8.*]I=a#Uh2C0O8UM]^G>/C,is'jMfWX7tuYL?$?tBn&7XSC=0JGHapbl(E,!K;3?:2e?LT)Urns:<b?@_B;Y"r/f]'*N5'9I>rTj$pjoN?e:hd19+n3/<#O#+Y)%#X/r>#n%C=kPc@Wl@"6e:E^"r&lp:f`Xjf5:>L5j?R]b0Za?>D<d--gp%B3+_QR]Qd+^'G"@rE8cNP.,Hg-*@JpHjd=<l]!mk75UIOo&):A(pB.TV-'*LiW69Q`(SBjkM?.44C35C?&UK4]X8rUI11,W^CJD*`lN9YhHR2&g_)3lMrb[hu/=[6jnKu[-c"`8#=%Z*-N.#pk?lk#r.uok3"WjgpJj:n4@5/_LMZQG0SBV&$m(7T?a33r.\%8esWr9,"hdD+(XEnQoDHSW16T(BeWd`AQ+h`/O[u7A/X'8D>=2.BjtL[dLG&S4e*eAf=$Sb]aEJO!cHP^5B#taTk1nk>(sd*T1f)R6!+.d(:np)<9Nf6/fpUPfo.m)*%%hGpU3\lD.%^/K(Hi;%V+s";\s(X+t?QgX^?]!R)"42K!qat'5OVE@$@b<g!M6'P8oV-[OJ[fD7D#RV66FU5"A%_-&t/JS/jRU`H2R%#lQP<a/@;qdhQsL);t6EE2Oe@\'!\Y@.hd].#F<[)d]/BE\6b]oJU&^q::Fu=KCJrjjS0JnM/-"N@\q3f8DrG&M"?E-i9:.UHrNJCGE'k]V6@T\.Himq"OcO[SJ-#NM,DNnB$jK=GQU-Is/XmXg%Ps&,gaHJqIlmn:-la`X%4'#aZ*qrEa3m?6;5Yg9Q$lg!3gmA5I/9B&,%L#E$VSjEgFn#4n1!HV^dhfAj;(HNXW#7Xte<Z/f-O"t-'_$Rb6,F;1+kCQKVtjJY-%;/gN/<aktn`Rd^H(L?At([-Ll)n4E4IuKQja^Ka45@"bLkHAS2B4Crj#LZKcI"U8bh.ajl[3]]]Kf"foL_[3V[Hr&)cs.7T./B8IYoh8tBM!=Qq#c';I%5-VR*LXa4YC[T')+FON[*pd9=`tHlCpPrZ)"9@45#;21T3GP%:fJNM!\6d/HQh(]*8oipMS"*9"!2Y^H8_t<NKi!I0@A;OFj\YGmM@:e''jWMu;a1D5RA$P/93N10XGB$urEo0,uVP3t`2*<Me1U0>14l#C(*p@!(bs'eIF&]_T&04o<*EgjWra**oU8493`T5mPj)j\*mDZZpV>qpl6F4;1';2+ITC3+B]<hrNuclZeNW6:k63@^D3-CJrOpANKq/krF_srbVI$WIJ%mKCil3rrEHe"?4;aTk#!4e$@EV4=DJsIBu@$jEXod2J]7T1$(MM=7["-Vd@hEps=ktCl`+MlG+N;HB*t*K[uk>Tr(,'9%p"!qchc<:YMNkpa]!A'W`oZ>BCL3c^2)]9%IsOr=c"ZN;VRU\ok20/t?bp4tN@O%lF1Gj"U?$bXUZ6TYdT0j[RBVVDIa(/K$up'VGo\@RGOWoq%)TS!<fVVVuRuNCO^36*Ld\(eNV(?*HVg_5YX&"Vt*QDd?f-177rAC6of88N4*L`%,\]Z)2('jXS-)dh0f]<eGD*E`7F<\K%Er:YkqB0TWOOcaXGXaHQjuQMabb#='D_o_&MW[UR!@U\I/s0?PkfV6S7qGgKYBpJ?Rtcp;FDbdt0"I&nkjq[Nd]"!@t!d_$<1\N-t2+D0-W!V5GRE6[JBTe!N6N/iA5A:,e7*9#sZBmtod^VFdm]013nT1^'?r\,6Dr.p])a=Vk<fLuCAVEG`EnSE[ZX7T1bY+_kFVeU'0J9Q94EWt!`*U"t]$u!esXl.'u`I"Fe)%Vuq*6P,fG$3+^f<-7p>Icpj\Ul+("*?&B::K6_>IT3/ku<SDIKTLGMdc~>endstream
endobj
67 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2539
>>
stream
Gb"/'D/\IS&cV3*0aR,HQd@iI?UV1g;-]=A_/0bUmL04!r+/=",UO4,a!Ijd^V8%\Oq_L)S00J?I-;Se)9_-ebVM'$1Fk`lrX8V8fFe)BQ<q9@,XT(JPDK1)DSN&uhHkT>n?XMLo9fG,:4jh4k;#`kK\jDQn.Rif1mGqC-6_b)8M^0E:%'`i"&nR&M>;+\+,bLaAE:eK@7btQ61'D6&;*pT^l3/T[!5U>[rS<+\nMMDm_WO-,.RV2^&BVm_Se%=eu`[\<R@d9ejiZ,(NfO;h1!WRX`s=!>Whg?1DL)Ed[.No<83K`A?Gi_7t7:\eK1]/l`0Sb)2jLB:2;XYo0]:g&!h0Q3;Pj[UF=>uS)4;"EVD5]<+O&OK.TEP/:gI8(^oo01ecp,!BpNQ%-nB/LN(C%/8WHEYtm;odd9L^5bqESWp(78>(,VC<#I/cVqObPZ;[SqYA0hHVjad:%972t8U`.)P/W3j1)6u3g<+b2oi\Y?+,7"YA,'Jb3:kY];-8Ug[O%%tIshpi=b+'r2F:ch6DR7B8rIoV?H]'>[B^heIW&4Zh,ZFHTm5)(h.B"un\l5cRP*VCoWi.%];i#NGR`>p=gr]IQVeB?!FR"@NhJ&[Y*eVmLM^#kZHfCp9a>C2hfBe5eTaEBH4_(Ur;>dHKh$n*DSOSF;_.^MepY[/?Ga+'<l8h.Pf&O'oQqlg=SrhH)^E*10%#Nn.mCXdGd&jD(s\SOlQbB?PjgaK%a\)FD=q8SE#F@Y0HP3-_HOWe!1QhSa3S7F.a,eF>H)/XBeNc"f@g4N=Oh3`8el*MJpWXL/=rFr[#elmAe1MiK:>pQ5H^GM2OeG].q@De9mrPu?4&@-_[/g@hF?i%J-D*I3Lg33fGR3.:B.kN9_.OI255RFEF+[Q</tCOLLQ+d-2sb)4Me^DlZ&R%BCFsJG^O-i[n)bC[V@Xuql3WJaGrIN^Jh+PKY!^!FBpcig(q/uGE7mK'M`d8Y>7WkCb$JuX!?X3a(uK,<&=0&X!<\>e,=-u;BD6TAW!qMTCUruEqIX$NX2NMG8[#hSu!*3cHbf;T(:nj#h,:VoWt=#$nWNRjQBYc$.b7jN09!2Xl8(boC+V$!9X.LMnkqC37"U&?jSHU1hk)g73c_3*V!WY9#UW6)U4S/H#mN@bap46A`iUt-D$%S?hjHrUM$2%cpk8")">WKdo_6G,rf*7:-7gKq+GXu-t5`CMsk<CjqOFIM_@L"m.\*YQleQb]!E,o[kLKU.B?^]Y.2;,Z>*'Ge%;btm!c[difp!\\;CdnNMJ,ql.`?,\C:jY/F09E$bZY+=<;A0JbH2uqkA/>bmQVdrh)=DpZMI8j*3&FVj6K$d8Z'r:)Z%]a9"Ih?jWUoWcUB0O;//(jXgloE#<IBAo3^L;?^q$S$H5$5p8q`r7Ye9oU4#2pff4nUgn2r:7^VT(`JG&7GQJs&23itLV\cfO!$"RPo8eU2+IPp-Mnb<@6WX_EjKK1`j(c]l@V)qYnJ:&FI?Y\8oaFeD?7Fk_AGdL)!9kB6$7p'cD\gZ4bsX=m#4l*&fb'tZ$_"jGld'*q>$6Q_+roWEH&5D62!7[C1jUEbnd)l0!?,0%Q.Th`Iib$4cHIahbb4t%Ea[PM:5R7ZuB,MK]!l<Gd<:M%rKeu^KpLW+KF!`k<U.pkd&.[SK1,DLOa;BGL5^f(2_Vd6s:_LglOG?XON%QR8C4'9UL0@*_s/A5bDo:-r6HP`-rNe",(8c4?9U[$#6fM.m">F:6BEEs'<0q0OpS3%;g;[e'KE(ZH(M3n"F5j>9=_BN$di$L8"J.b2$N_l*a*#<qG>gm/1Rj]sE[N9GlMYG^?Bt$;HDUE3O7a`EacEa#pPQ;4<G8pqQP$1@:!_CkD0.W*f+cqB`mYrM"Q$gj?OP"d@]U=oju`11tlg,^rJjRO'E#PN6[!*VmoMT!:!^l@Wn(QSptiFZm1k1ece?[\N8iHS2l`N_WH!,'@F271*/>N7pprAK<d_Jffc%[37#Dk8>0#FSfDR7&"oOka\M4Q;SX88&,_>nJsiDk^aBSUMu0Dk'p`S<S<#JDf3AX2C3<h"UE57?YAA'ZjM!n!qhp(%k\3uDIut>(@:,MXI]^(O5*jrHCd6D`qRt9iok+gff<skE=99W=Bru%\i(E4+Z(t`m,>fcc>_`0j"##/(%.e=mZp[RHWditp=4fa'mt<<5!PHI'OSNmik4FKB*dns4V4qB44@>YY'P@Qh5S*.pY8>(=s]/nBaa2.cjcn/YOC7(BU3ftlgW<tq0*/18).Cp1TZV6&:+,/F;9Z:-+0PF)t&?BE1N=lX"Zft1<@8%3e/o"@/!DT<Ms'HRH42h<\b@GMI*L,5d(8S&/f:+\7$kV@7r&h\6Cm/VDfM6Zt7`I)>C4qX5:;73,"/Lq06dqY<1Q]K6%6sh8EQ;FSno&cVrBrCVEdg0n7<?9OA=Zr0,#"^u<JF]llWeI[k?Q%CgEQQ;6$/`q*psdXg`"dCJ:N5Fo=\2cAldoJ=E&&A-9HkNR'a'DhXje5)a],0Bho\h)j;;e<Q8+#k?[A,~>endstream
endobj
68 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2822
>>
stream
Gb!;dCQI5i(&bk]iZd#,jFEsbHo"&cXPMNJ)s:Y1-jo=-&N,_b;l%V\=&qQX\*)NaP+m-O>Ji1If!-H.1q[lOkFQaMJirrYbl@8TdBa!>I3D/VZriLth2iC:dLV7o%i9+%7",o7Rtcb9Ab_5_,`Ls3b6p8'_aR!k84hmkNhRpZhb&3Ad2Pc`#8XZ&S/[>:p/5qKhH8iI5u=oH#=S$F0ppBu8$hN%^QhIBd]4jAl,Jbt'&NQTo\s5lk=9^S7GXn7(HGc&Z97D=5G?%X>("Ku)XkPZ\T%1XE`CtbPFgB+Y*t5i/kbjXIekkVWocj_>urN]-Y'E]gXFm;UoDbWF1iFYoqm5$)b#36g&*?547%tj8jnOdE3b0NU)81G3QHa,+Ru3\]9==t!`&%k)><$R9sHAuRjB[=<*@XE;7fhmDe4X?Mi)u?X%'Nd[@prrH<moM=uMkEdNkmDSZOQ7>3kcsB%PumJib^*JZpl!3LU6>WA#CnBJ>QOLL&kMW<Zf;';@!D+d*\9d`abVZR=eFUAr$SISXfT;<Gl"m%jm$Cu*ShDX.("2butZC=KAc3^oN-*CrS"r6/a9q+_jHYIUI?j-WDo.r#F9!=rV`nliM%Y6Q$#4=amuM1Xs!6\fMU.]UNWp'r-_WmY'ND'@*n8F'0^KYN*,H<9V*;YZ[?"kdZN\5^$*oYegip)K/[B-F(iJS+3-*fu*YH!0L"C.2p;>L``BIR7ts1UB=!O1uS\A)VZHo%K>mjk9+Sk'(/l@Ho'AXu-&d@n"A._YE\8Q7od<bG$PG\tU:<e%2Il)]W,TN,'%D!Bgkg9!sd-aZOK&=h=7&c[MY[H;bP1DqW`ROWR;d]#pa`ot<AjY)k7u>Bc?(W,?UFCfVf_oq"=9eAd`BD-XjS#M2/,HPm6"93sF,j[WJh3\P:)2+jWG7CsSVd(<-6lqU`Gs&?H7&CoU":Ml"o<LRM)J$^WcGj\GNL2,Y$pm_._$Ue]b%,Ph&YQe:kX9X?^#Q,_97?#P0IhMCci/T`jckDR*n`bsNG\0DQUoqbpSspFe/2S_m=fS`t2r$dlITs(p``oi<@(c0J$iu<P&g]I/h\@6XPDebiEr]-uiN)WTjmA.*;mZS:o,a`5Jjr=Z=Z&`[`V0.+_"\d4/DFFERQ&AUmk0o7H&GY25RFk?7lMb;Ym>A@f>\i(FG4:.DA;Tj."qMi1\'^-q+4%QljpLE;t,k2PFJCW+B[l+5DT@fh2:qSX:fT%i.1L0(S7m@);/]#BB[qh'lubG"Ttf0Q#f;(?GPn;P#(-8X?LTLC+K]ZkSZP&&J)hN2uJ$s8_YV<2A,:8#(3`S<TZQQighZGV]Fp/ksN3L!;A/c;tsM,5"6sG,")KT\)5es.IW%pDC+nobtR"W0qsTg/(OmN+u]KQ.,*7c`:h7K0aOk5GLsN9FSmou=!XD;gsi0%CTF-$D@b(q-g3ug2[H1afOX[1*f!NR!@gGi*p\jN\a:+NSQaRN_`VEj^`W*mlCu'!khRhdAIBRGRFJ'GP5>Yef^_ftHs^qrl>>@B/"EtGFJtZ5$2htVfa7h"K^6OmI%Cs4ThPZ<i4%B8ooK5B3-Cg:9qtbHogrUFh(oG>VQ$&1%c9N+X;%1r]Te2Jbhp`L6L4i`<VcN'rDD5h?e->D()!]X.[pcY&d2WV<GE@c\0OaL[u*[H<f4A]A*[UA>!_Jc0o?%7XtXVaMK5*f:6J&=7\b&f?,.l^KgsNScOh#K-GMJ(>UbRGNs$:I9o6>A`\`Q]DM69EB?&TNN3oa]Feack,_i5j9`a-:\4+*ZbhRR?$`g-j@+`[*K9C4ZHCBjFM:9tao$)7+[$&J>*Rgr6,99_;>DWb?("aIN0;[7.j5:"r&II/o!AKd,lKi"nmX/NXO_#!?,BaRdcKN'Dc?7-_2,S?L=QNa&,\5OQk93Fc*LIO_n@dS[\D84fJfm]-;Wa[V^T'38V<2+G0ILtXOE414]oW.+c5d!E;kU[h5AWeaCiBp%VY/[F4nV\7/MP[XF[UduMn7A>.CAMfOt8(cjd9"][)-ca!N:M\DDtd3iIbqbg$A#^ekaD%OSiIA.EqgqWbE$@?U7?Fa.tQk@O2K#p]2BE:5\RgYH?J@&I%6TC66BdhJ=$t'l*jd3OT"9V6Y?,D?FU)/;fuRS^qn.gGSr&M!&1@Z,h;WHXLI[./ea5/,+M=?)J0d$m.=LqErOO!r1'GHr!uX-!/C]DI]Fk%,.PO!kI#"'eUgrnb%P/a9V1Fh;4<;J'f3GM9PA^;M:'$8$1cJiA,TTnI>eqlDJ_D<LX#:B<I%/8r%r>N[JWgqT]Oi4FajidUSV27Nh012tF:/T'ihXQ_8UN1(s]TqQ:\&r_jk^om$>8/3<t*q9hr'N$+odp7uFhn4],?iV`[aP4/#DpN=(cY28Ls%g/9h8jdJP-V9Nlh")L5:?[bVJhsqE?2>`(nkRkFPA*35KDNq0m?'6C)OG"Hq9;XCf,!l^T'nJ@/H1'Ddkp)Ci%'hnf=eRC)WD0u!3:=7DCqPd1HQn.r^;XUbnfG0HH!pobJ&d1-hZLu\f3M>`U+=YHAcB14=,t[a=FgNgIF7kUqn-p([`#qk9GF;B3oQpjOrPY@DLgcnT6MI5X'9@Em0=L/\BTVW+>OQ-s7b'r(OdFF4'aE38!8WIDAg6cJ<1BKN#u4HIo8W>`TqnP?NqO\5Q-1Lrn:6!b6O4m]1mnhgr!"\L`r\'c"FsJa\EU"?K-O)UmQ?1P6R/d6OL;./Wk6*dPN:.PKf\*?Q[no--^eo\HOtf@0JIWu_9G<eA$2;tg"$#l?ccIt4=&>Xj1WUh>`[HM5=@%YRqUVi0F4k0M.o~>endstream
endobj
69 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2660
>>
stream
Gb"/&>Ar7c(4Q"]3%1:t.4BqgMb%Hb%o-:5frj.CCLFDt?Uj*IRYE#O):GhafCqAEMrdTjDA2A8'-ra^R<(UMGE/<rItdd7fFkm.U0$N06qCB0'!WP-eN`<=X-6=,IMO5<*g<58BoqEN>_Hg]d(eG.p^-=`C._r-PE<5;,anO1dB=pM^_CE(0d"@0Z,d_I7XdH*9*.3eACc,o$q<7.)-q)nG#mugEiE5g?Pbn3LPqBb0`R!Trt>TFdQ]^0N2j!4kcC*#_.rk1Y(!.Hmoc?j/fp"1-ejY\7=iq[[]'XGC9iPpe8)_n45D<+TV?q=8e7B\Y\r1,B1JDNKgpV8/7@<WqA6\CpjR>[!s1QU?3HLM$sDLrMbkZ,`$OI]$hC&L9]Gt9Hif0bXBS(PKMd/RKhL)-5O&-(g5U]LgRYG)_+*!k<Dof>7MT+8\uBDq<4^H!P,q=1D[s9GHWdh"BKBlIC/n9]<fsQD0l7M3aHZF(Gi6LaNa^&f7Z_6`C.:2KI1ZjL/fo;ckEsF<++/$V_2HKKYaY5L[ei>D;Q4M12--!GS[UsT>W/^9E2-U9C[9hZ#sUJO<aA.Z^1!XNIlp1$Kdi:mSNNAdFTG_ZFLA#LU$>Yr(SbTMdY4E,VlN_ICJ,,ZK<2X]29.3Wkb+`V*Zc33klY.jG2J[JUcrpI[tQM>X'-BD<<oi+G.b[^MoP*%,?m$/&i^8hC3Tb(XApi7g,H)DY.De??,8t)mGh##/)$D'VbDGV)X`R"rR4Sf,$N>o<tugsAJ`+HBssc?ZW!!2OUr$5`JEr^;FT>qpG<\:MreoRO?;:@MU_#geYR.F1W4+dF=k<nFp4.1':5Rn2qmg[=JTc6\+"l^WgQMG7sj'0h!%i%`!qu_.nb,iMIp/[s.[6dXPL]Dgo:k`F/>>d6baY,,FU\,>`WA,^,h=p](Elg&&eUB$iETDQ@^%h"[1g6YOC"e4PlL:`5ncTGgEp.&"Y94hAq[3FfBp@]ta=,<L:dq"u*U5K\2jCNH#-[:!qZE3>DB\Y;sc"PX15dG-Z5=<8CU"9;B%>O#+XsNNuj?p@]-[f3IY5<@(j+!kqHERe2V#7%uTNfW^792JObe8%G_Nk7\H)3@030*\oJn71bWSB5o2aDR(rg,0#S1:T"WOF*sV\<o9MP:.>aBNjo.G+5oUl;mn-D0Zd1O*s7rUL0,R8p)'$g&Qgh:;)g\\knR/[iQ4=Rn$gWc^>hcI_3TMb-Z`,O'Y5[.]a)C0$2<l_dYB2B)(aM=pP5\ink\'40-T*;!'`&Jpf#eOY%XtNpA1UU#ns"=Bp>K"1TImd;HCBGl0%pp:>*.4:XNf^L[>q[ZWs.J)(L=?(_3nf_*kG2T>YOA6'k@YU4YLQGBWZfGL^8'chY1CiSB20L\dnZS\,3N:H9B7nKUk=C@@.s6^<Mq50K*"phqT9e+@=VJ0o\^HKI745)\T]dG5Eo+79.oWntMVflSpFM]\H>ZZ#`%ZgTF^^3>%kl#/975Tm#"kR=>h_EkT04(Z/EM3jpglKo'\[[5Ri77QYY,</a61Ce1@0a)&6.h*s`CqmTV/A%Yt)`#9(l=EW*&!L37rq?8&3YdS*91<rR0"cRmT2Fg/1q:&Ead$R%4.M&O,HZU0_SciRSF;u*+Rk'*E1s1&=VM(kf\Vo=^A4`$bbRmG5TuM@DKtN#2=na^?>p8*L<4;*i_^f[d+S=27O>=GnMJ@]3tk*g6GVU"SUlts^'I(0%eIY!$+qrp>]9Z`%2@6.&=[:X1FKc?is')#]If@go*'fAY!EBB['4hT$46,#^W0ZB"W(us`R%s4-D_-sa9?W3cNNWDDAD`D>Fl(*LD'aIWl"#`<-%gEL+QjQLJ49iUk=TI`+PbD[J^g$MY(>(Hm.ag_6=%BBT4Wj02TYr+V18M9-+Q)6h6?q[X>fR`CI(5GUWI*%U@(P/O?o6;>mf)E=T.L=E9TG7eB)nQA;A)K;l*63I4dI+:DamHNXCHfcHUOYc48Xb:(R6ila"699de)i60)\I(B%$Hl4Mf-hoG8M<-7(LS7NDk41uunnu@949.I#FZXPOWE1T]ppF,fSl2`IGfefOat>cIr>Xct*@sYKH<;DaF"U.=EBeh[$iJoWnQjVF.n.2_qJ!pU%p7$g?T=PsE-_'bHk=8jQ\N?Xib9Bc?5>9@p)[iqhn-oN;%S)"j8egi+,YTpJKkdKG%&3paP3`ZJ<AJRfa8<IfL&,kH)Ri:$_e`RkAfR:@I?s@D43VC28Y?(.n6_VS+MU-`S]ll2lOK"ij"d*m8.-9(&5$I.D-ou07#eVZ&#^o0Gen_!`eF'#co5;r./Nm;h5P#Uhs)AAcqD6l`!;oXa_K^K'ET:P.WXrJm?g(,L%IaA1b0RE1k0&!'0u`JgJ+`lC-lAeD+c*a5/"qJEp>Vh9dYV'=&sm;f\_N3q;UIriuNc=qZPYC^Cjqc<UoAp6b0^jg*caF"beU0eQ>]77hsuC_&kQs(OFIl<CP5]kVh(C7DmnrPZ(+(;&.FW!j1Cf]+@Q.HG3AZt5"@@skl&;"*LS8CS?s;XrJlN-kd)\spp4)U&@G2cpmN0l49?/0DfrY8l)b42QBD\%E%dm5EEb.1_KlD+boRa0[f1*/F%'l>\8Tqk`qGDiEo+^DQH5(f4bb=(&iA3<m_-1]rUll5>[YIKq#:0R3~>endstream
endobj
70 0 obj
<<
/Filter [ /ASCII85Decode /FlateDecode ] /Length 2015
>>
stream
GauHJflGh*'Rf^Wg]tGk&t()V1GaH`>rtb"B;q0\AB$86#t[f]630V-rqdaeMrZ0Zg1KW0('n1#m@858\bKe1DcRI@bin8\&bB\E+;Qp;c!JfND"$tePPCi<#37$qm"Qs\OV\6GrV9pK$#-_I;]&=NH;m`Y-MG3;0)'[E1%rClg7*-bQ:>aY:='pf>q@[-965XV:0E2Ubpo/%Qg5BYMhYQhR6t%^'GGNus.JroT'M*d_RWX?ejW'K2(rliTqB]u,L)gK$a"Whi*7u4[W@`&g7(iKSI&;[c?Le0j4,f)/^t5@h7C\*\/C44Cpn+@2shOV?,qr_?>oZl?OHAWcK9=Am'&Ql.:rmd@$8bs(.QB'B6)5;nRF3\dQ@8EaZ!q9OC8YpFX^q2A/")eo[esZZkb,)F[L188mI:c'pS5\cpGj3nm\j8b.M$f\Q!si.Pa`2c=pe62Cn=EH*2%=E$pGi#iJ8rL79MBHA5Sk*>U=E8,&bAC2DTLm:3A?]qRmT02=XeVqD:='8g,>7Z]PLl99GL7t"Rsa9l.+88`+Y28-2O7c\[En4%*FB5''m]_$fY-:)Zkojg[-(MCcjBCV4?SltecZT^e@g8g:l*hUl0'MkLB21&GAc^I886';p&j5qQ'IJ]U#9jMN_Z?sq\]%*@h!U1>#n,pc@dXruojq!@[3`FE,)VL%(X!_*)$HTfk_80U.B\K+_`3CQtf<RYEEflVU/Z>W8hY3Am("V70^*Uf0r0U"p3jUE?`3PI^/X=uHeT`[<CK\*eF"YY!.udA5p),&qP*8(<ch:N*\G0SjK28Y6imXH/4PN@L:J;Q#:o`L_ALh'h#>-O>OYn@S-O['r*/:eM'Q;nI0B&DU1b2JZ)K'L.OU[oB4V66oSseE[UJ8k_d$-Vo#9^@_K@%tc8*BluKoY>o*fKNHn.c%YbeOeW40h7ukL"Q/S=._4@;`nl,;(eZXT>/JQRHELG:CVt7W:d/[HRVE'F7^o/reX#p!OOlW61L2^,fbA\$^[7H.^2*>8c0R`dskaJ,f``3d>_BG`@HXjhP>4c^u#O^h>d'3WYURO.8$5HtF&n&.O$ile:]d%@\EuJMpaqh/f]`%eE_*>RPOi<0jd_jH$ZVe\DL,*kl&KOC<1%2uJ7(&o3VP`95P\mW]kAhspU6X2_V0Aj`Lj&9o+aW9oRf`P&\;DKj`W]8,8!Do+4%`Z0Go!0/5.>9QJ3g\"aM`jEbK<]1^F<tfG4()b+@('WEM)pmo2`YSel@ehEA_T;-"]=YdMkl4ePJq'Xj#c7WhP_Ol!7lXHD:%5GkAKX"S5Z.,61JN9He9-n1a5RKDp]1jYWdC'67NqW.JF-#U\J3am"%nrLltTEqk>3J?H&0>!f4JSR*/K'sL^J8^PWp2j;Y*6H,rg1lNGr%kLT0EJ]nQI9jFriA;BT_WZ5*=+ddZ:]50.oucGBK?GbO$d=u71t5(P*8\^"0Z2U.tWeg55M;H<QA(FF4X"/hu3o7>(\7"_r%C'1sJhJ>(#H4L2]O$$S_BV**1B(JleEq]1H8-F,6;OB?G'g\oAHIHRG&s8GWDl5+E"3_.9IN4_rN-J:5Z_%F1f36$YhAQ]XbI^lJhhm@,CmrPoMGRRMT/!Sm\DB(4UC4_Ki:b\H9W!@&eW[-\RHF\X[tb$Th"O0[lE\@R'>Bkc$j?I^G](^-%8%G2/Bs`jms#(\a9\Y?ap.0Oka3O/$G_:j-!l2\M)Soj_U+,ML?Tn@E;i^RUN%B=5G+@h2fi$XVibWOqOpLeeIm+FZ92OQYXG[]A&n=DDO#)<[T9-^l4]d7"`ogr(:DS"=W&jU!+s[dm?8K+.X/KOVf.$tp_h>QADUqC+aO:)E*ZkeftiXDB"qQ01t">lQ/YF`6k3GF2(^UbToT8pjt1\`B7mTtDX===U&8(q4k3];2'\"[Tco!R#4n<m#([^fjLG50-2*P0X!HmfmHE/Y7iM@m$62>M4\0tI4l,SUhW,X(HdD!W+M)79+!A,YA!3>\CWZ5o[hE$#q\qTI3%+~>endstream
endobj
xref
0 71
0000000000 65535 f 
0000000061 00000 n 
0000000122 00000 n 
0000000229 00000 n 
0000000341 00000 n 
0000000536 00000 n 
0000000731 00000 n 
0000000850 00000 n 
0000000965 00000 n 
0000001160 00000 n 
0000001355 00000 n 
0000001551 00000 n 
0000001747 00000 n 
0000001943 00000 n 
0000002139 00000 n 
0000002335 00000 n 
0000002531 00000 n 
0000002727 00000 n 
0000002923 00000 n 
0000003119 00000 n 
0000003315 00000 n 
0000003511 00000 n 
0000003707 00000 n 
0000003903 00000 n 
0000004099 00000 n 
0000004295 00000 n 
0000004491 00000 n 
0000004687 00000 n 
0000004883 00000 n 
0000005079 00000 n 
0000005275 00000 n 
0000005471 00000 n 
0000005667 00000 n 
0000005863 00000 n 
0000006059 00000 n 
0000006255 00000 n 
0000006451 00000 n 
0000006647 00000 n 
0000006717 00000 n 
0000007045 00000 n 
0000007322 00000 n 
0000009376 00000 n 
0000011520 00000 n 
0000013601 00000 n 
0000016007 00000 n 
0000018385 00000 n 
0000020649 00000 n 
0000022420 00000 n 
0000025008 00000 n 
0000027942 00000 n 
0000030250 00000 n 
0000033209 00000 n 
0000036085 00000 n 
0000039053 00000 n 
0000040896 00000 n 
0000043977 00000 n 
0000046660 00000 n 
0000049483 00000 n 
0000052434 00000 n 
0000054670 00000 n 
0000057602 00000 n 
0000060389 00000 n 
0000063543 00000 n 
0000066602 00000 n 
0000069634 00000 n 
0000072650 00000 n 
0000075116 00000 n 
0000077693 00000 n 
0000080324 00000 n 
0000083238 00000 n 
0000085990 00000 n 
trailer
<<
/ID 
[<dfa935b6e538c774414a80da6dfdf761><dfa935b6e538c774414a80da6dfdf761>]
% ReportLab generated PDF document -- digest (opensource)

/Info 38 0 R
/Root 37 0 R
/Size 71
>>
startxref
88097
%%EOF

[alphabet-analysis-20260813-223159.pdf](https://github.com/user-attachments/files/32162088/alphabet-analysis-20260813-223159.pdf)


## Disclaimer

This is a research tool. It is not investment advice, it is not an audit, and
its output is not a substitute for professional judgment. Language models make
mistakes; the evidence verification catches fabricated quotations but cannot
tell you whether a correctly-quoted passage actually supports the conclusion
drawn from it. Check anything you intend to rely on.

## License

MIT — see [LICENSE](LICENSE).
