# TNU
Tradutor offline que vira número e traduz de novo.  
5 MB, sem internet, com IPA real.

Instale e teste em 30 s:
```bash
pip install -r requirements.txt
python tnu.py add -w vida -s pt
python tnu.py add -w life -s en
python tnu.py trans -w vida -s pt -t en
# → life
