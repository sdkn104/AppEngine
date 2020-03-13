import imaplib
import email
import pprint

# 転送元メールアカウント情報
src_mail_server = "imap.mail.yahoo.co.jp"
src_mail_user = "sdkn104@yahoo.co.jp"
src_mail_pass = "gorosan"
#src_mailbox = "INBOX"
src_mailbox = "Trash"
dst_mailbox = '"00&MFQwf3ux-"'  # 00ごみ箱
#dst_mailbox = '"00 &Tg2JgQ-"'  # 00 不要

# src_mailboxからdst_mailboxにメールをコピ－する
# コピー済みのメールにDraftフラグをセットし、次からDraftフラグのメールはコピーしない
def cleanMails():
  try:
    src_imap = imaplib.IMAP4_SSL(src_mail_server)
    src_imap.login(src_mail_user, src_mail_pass)

    typ, mboxes = src_imap.list()
    print(mboxes)

    #src_imap.select(dst_mailbox, False)
    #typ, [data] = src_imap.search(None, "ALL")
    #for num in data.split():
      #typ, f = src_imap.fetch(num, '(FLAGS)')
      #src_imap.store(num, '+FLAGS', r'(\Deleted)')
      #src_imap.uid('store', num, '+FLAGS', '\\Deleted') # Deletedフラグが設定できない（理由不明）
      #typ, f = src_imap.fetch(num, '(FLAGS)')
      #print(f)
    #src_imap.expunge()
    
    src_imap.select(src_mailbox)
    typ, [data] = src_imap.search(None, "ALL")
    #print(data)
    print(len(data.split()))
    for num in data.split():
      # skip for messages with Draft FLAG
      typ, [f] = src_imap.fetch(num, '(FLAGS)')
      #print(f)
      if b'\\Draft' in f:
        #print("skip")
        continue
      # copy message
      src_imap.copy(num, dst_mailbox)
      # set Draft FLAG
      src_imap.store(num, '+FLAGS', '\\Draft')
      typ, d = src_imap.fetch(num, '(RFC822)')
      # print for debug
      #msg = email.message_from_bytes(d[0][1])
      #print(msg['Message-ID'])
      #print(msg['Subject'])
    
    src_imap.close()
    src_imap.logout()

  except as e:
    print(str(e) + "\n")

# エントリーポイント
if __name__ == "__main__":
  cleanMails();
