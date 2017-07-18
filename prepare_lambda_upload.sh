rm -rf ../redash-emailer.zip
zip ../redash-emailer.zip ./*.py
cd ./venv/lib/python3.4/site-packages/
zip -r9 ../../../../../redash-emailer.zip *
cd ../../../../
