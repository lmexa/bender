import sqlite3

conn = sqlite3.connect("mediabuy.db")
cursor = conn.cursor()

# Создание таблицы
cursor.execute("""UPDATE users
                  SET paths = 'mycom | adsbalance, mycom | adsbalance/hustle castle, mycom | adsbalance/hustle castle/китай, mycom | adsbalance/hustle castle/declined, mycom | adsbalance/hustle castle/approved, mycom | adsbalance/love sick, mycom | adsbalance/love sick/declined, mycom | adsbalance/love sick/approved, апрув крео combo, апрув крео combo/экономика combo, апрув крео combo/виталий, апрув крео combo/виталий/согласовано, апрув крео combo/виталий/не согласовано, апрув крео combo/марк, апрув крео combo/марк /не согласовано, апрув крео combo/марк /согласовано, апрув крео combo/сережа в, апрув крео combo/сережа в/согласовано, апрув крео combo/артур, апрув крео combo/артур/не согласовано, апрув крео combo/артур/согласовано, апрув крео combo/костя в, апрув крео combo/костя в /не согласовано, апрув крео combo/костя в /согласовано, апрув крео combo/степа, апрув крео combo/степа/не согласовано, апрув крео combo/степа/согласовано, апрув крео combo/ваня, апрув крео combo/ваня/не согласовано, апрув крео combo/ваня/согласовано, mycom, mycom/american dad, mycom/american dad/disapproved, mycom/american dad/approved, mycom/american dad/project creatives for test, mycom/zero city, mycom/zero city/согласовано, mycom/zero city/не согласовано, mycom/zero city/archieve, mycom/combo, mycom/combo/combo, mycom/combo/согласовано, mycom/combo/не согласовано, mycom/love sick, mycom/love sick/ml, mycom/love sick/ka, mycom/love sick/nm, mycom/love sick/nr, mycom/love sick/as, mycom/юла, mycom/юла/неактивные менеджеры, mycom/юла/ml, mycom/юла/sv, mycom/юла/aa, mycom/юла/sa, mycom/юла/ap, mycom/юла/zv, mycom/юла/kr, mycom/юла/пруфы юла, mycom/юла/vz, mycom/юла/vs, mycom/bombastic brothers, mycom/bombastic brothers/kn, mycom/bombastic brothers/ea, mycom/bombastic brothers/ak, mycom/bombastic brothers/nr, mycom/._icon,mycom/pandao, mycom/pandao/._icon, mycom/pandao/._mk_, mycom/pandao/mk_, mycom/pandao/av, mycom/pandao/._icon, mycom/pandao/nr, mycom/._delivery club, mycom/._pandao, mycom/._юла, mycom/._hustle castle'
                  WHERE email = 'a.vorvul@corp.mail.ru'
               """)
for row in cursor.fetchall():
    print(row)
#print(cursor.fetchall())
