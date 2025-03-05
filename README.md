# Lending and Borrowing Money Note

## 概要
**Lending and Borrowing Money Note** は、個人間の貸し借りを管理するためのアプリケーションです。お金の貸し借りを記録し、管理しやすくすることで、スムーズな返済や管理をサポートします。

## 主な機能
- 貸し借りの記録追加（貸した人・借りた人・金額・日付・メモ）
- 貸し借りリストの表示・編集・削除
- 返済状況の管理
- 貸し借りの合計金額を表示

## 使用技術
- **バックエンド**: Flask (Python)
- **データベース**: SQLite
- **フロントエンド**: HTML, CSS, JavaScript

## インストール方法
1. **リポジトリをクローン**
   ```sh
   git clone https://github.com/black76-yy/-lending-and_borrowing_money_note.git
   cd lending-and_borrowing_money_note
   ```

2. **仮想環境の作成（推奨）**
   ```sh
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   ```

3. **必要なパッケージをインストール**
   ```sh
   pip install -r requirements.txt
   ```

4. **データベースのセットアップ（SQLite）**
   - デフォルトでSQLiteを使用するため、特別な設定は不要です。
   - マイグレーションを実行してデータベースを作成してください。
   ```sh
   flask db init
   ```
   ```sh
   flask db migrate
   ```
   ```sh
   flask db upgrade
   ```

5. **アプリを実行**
   ```sh
   flask run
   ```
   アプリは `http://127.0.0.1:5000/` で動作します。

## 使い方
1. ユーザーは貸し借りの記録を追加できます。
2. 記録されたデータはリスト表示され、編集・削除が可能です。
3. 返済状況を更新し、負債の管理を簡単に行えます。
4. 借りている・貸している合計金額が確認できます。

## デプロイについて
現在、本アプリはローカル環境での実行を想定しており、デプロイはまだ完了していません。
デプロイ準備が整い次第、ガイドを追加する予定です。



