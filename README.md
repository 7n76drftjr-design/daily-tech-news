# Daily Tech News

AIニュースとITニュースを毎日まとめ、閲覧しやすいHTMLとして生成するプロジェクトです。

## 方針
- 配信カテゴリは「AIニュース」「ITニュース」の2つ
- 仮想通貨関連ニュース・価格情報は扱わない
- GitHub Actionsで定期実行し、HTMLを更新する
- 手動実行にも対応する

## 実行
GitHubの **Actions** から `Update Daily Tech News` を選び、`Run workflow` を実行してください。

## ローカル実行
```bash
python scripts/build_news.py
```
生成物は `index.html` です。
