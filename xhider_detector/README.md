# Xhider Mode Detector (v3)

Tool nhan dien mode obfuscation cua file `.lua` da duoc bao ve boi **Xhider**.
100% Python stdlib, khong can cai thu vien ngoai.

Hien co fingerprint cho **41 mode** (v1.2):
```
Abyss, Abyss2, Basic, Env, Evil, Flow, Hard, Hex, Ib1, Ib2, Ib3, Ibs, Ibv,
L1, L2, L3, L4, Light, Lightrew, Lightrew2, M1, M2, M3, MaxSecurity, Me,
Medium, Normal, Ps, Psu, PsuHard, PsuMax, PsuMedium, R1, R2, R3, R4, Rz,
Strong, Veil, Weak, Wrd
```

## Cach dung

```bash
# 1 file
python3 detect_xhider.py target.lua
python3 detect_xhider.py target.lua --top 3
python3 detect_xhider.py target.lua --json

# quet hang loat (batch), chay song song
python3 detect_xhider.py --dir folder/ --csv report.csv --workers 8

# xuat ma tran diem day du (moi file x moi mode) de review bang mat
python3 detect_xhider.py --dir folder/ --matrix matrix.csv --workers 8
```

Output mac dinh (gon, khong in header/version):
```
#  Mode             Do khop
------------------------------
1  R2               100.0%
2  R1                91.0%
3  Ib1               90.8%

==> Mode: R2 (100.0%)
```

## Dung nhu module

```python
from detect_xhider import detect_file, detect_text

res = detect_file("target.lua")
print(res.best_mode, res.best_score, res.is_confident, res.likely_unknown_preset)
```

## Nhung gi moi trong v3

1. **Lop dac trung thu 3: entropy/thong ke constant-pool**
   (`constpool_features.py`) — phan tich TRUC TIEP noi dung chuoi/so duoc
   nhung trong file thay vi chi dem cau truc: shannon entropy cua chuoi,
   do dai trung binh/do lech chuan chuoi, ty le so nguyen/hex/thuc. Dieu
   nay tach duoc nhung cap mode co "vo harness" gan giong het nhau nhung
   khac cach ma hoa du lieu (vd R3/R4 dung hex_ratio~0.97-0.98 trong khi
   R1/R2 dung 0% hex).

2. **Sua loi "khop gia" khi ca 2 ben deu = 0`** — truoc day neu 1 dac
   trung khong xuat hien o ca file can nhan dien LAN o fingerprint, tool
   tinh la "khop tuyet doi" (1.0), khien script Lua binh thuong (khong
   lien quan Xhider) cung bi cham diem ~80%+ mot cach sai lech. Da sua
   thanh diem trung tinh (0.5) cho truong hop nay -> file khong phai
   Xhider gio chi con ~50-55% (dung nguong canh bao).

3. **Canh bao "co the la preset la/chua co trong DB"** — neu diem top-1
   qua thap (<55%, thay vi muc binh thuong ~90-100% cho file Xhider that),
   tool bao ro la co the day la preset chua duoc them vao fingerprint (vd
   preset "Hidden" moi thay tren trang xhider.xyz ma chua co sample), thay
   vi ngam nhan bua thanh 1 mode co san.

4. **Batch mode chay song song** — `--workers N` dung multiprocessing,
   nhanh hon nhieu khi quet hang tram file.

5. **Xuat ma tran diem day du** — `--matrix out.csv` ghi diem cua TAT CA
   mode cho TAT CA file (khong chi top-1), tien review lai bang mat cac
   case nghi ngo.

6. **Fallback version thong minh hon** — neu gap file XHider version
   chua co fingerprint, tool chon DB version GAN NHAT (so sanh so
   major.minor) thay vi luon lay "moi nhat" mot cach mu quang.

## Nguyen ly hoat dong (3 lop dac trung)

**A. Regex "vo harness"** (`features.py`) — dem so lan goi ham runtime co
dinh (`getfenv/setfenv/newproxy/rawget/bit32.*/pcall/...`) va ky thuat ma
hoa hang so (dung hex? bien `v_0`? bieu thuc nguy trang?).

**B. Token-level structural** (`lua_tokenizer.py` + `token_features.py`)
— tokenize toan bo file, so tong so token, phan bo loai token, va 300
token dau khop bao nhieu (van tay harness on dinh nhat).

**C. Constant-pool entropy** (`constpool_features.py`) — thong ke thong
ke tren noi dung chuoi/so thuc te (entropy, do dai, ty le kieu so lieu).

Diem cuoi la trung binh co trong so ca 3 lop tren so voi tung mode trong
fingerprint DB, roi xep hang.

## Da kiem thu

- Self-match tren 41 sample goc: **41/41 dung top-1**.
- Stress-test: cat ngau nhien 12-25% noi dung cua 22 mode de nham nhat
  (mo phong script duoc bao ve co noi dung khac), 66 lan thu: **100%
  dung top-1**.
- File Lua thuong (khong lien quan Xhider) gio bi phat hien dung la
  "preset la/khong ro" (~53%) thay vi bi gan nham vao 1 mode co san voi
  diem cao gia tao (~81% nhu truoc khi sua).

## Han che con lai

- Toan bo 41 sample deu bao ve **cung 1 doan script goc** — chua test
  duoc voi Xhider that tren nhieu script khac nhau ve do dai/noi dung
  (khong co quyen goi API obfuscate that cua xhider.xyz tu moi truong
  nay). Neu co sample da dang hon, gui vao de chay lai
  `build_fingerprints.py` va tang do tin cay.
- Site xhider.xyz hien co preset **"Hidden"** va menu khac mot chut so
  voi bo 41 sample dang co (thieu preset "Hidden", co the vai preset
  R1/R3/R4, L3/L4, Psu*, MaxSecurity la ban cu/an khong con hien tren UI
  moi) — file dung nhung preset chua co fingerprint se duoc canh bao
  "likely_unknown_preset" thay vi bi doan nham.
- Cac mode co harness + ma hoa du lieu **giong het nhau tuyet doi** (hiem)
  van se can them dac trung khac (vd chay sandbox that va so sanh hanh
  vi runtime) — ngoai pham vi static analysis.

## Cap nhat fingerprint khi co sample moi

```bash
python3 build_fingerprints.py /path/to/thu_muc_sample_moi
```
File sample dat ten `xhider-<Mode>.lua`.
