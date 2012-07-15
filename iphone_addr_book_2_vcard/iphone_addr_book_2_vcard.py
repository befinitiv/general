#!/usr/bin/python

# Copyright (c) 2012 befinitiv
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#   - Redistributions of source code must retain the above copyright notice,
#     this list of conditions and the following disclaimer.
#   - Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   - The name of the author may not be used to endorse or promote products
#     derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO
# EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
# TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.



import io, sys, codecs, locale, time, datetime
import sqlite3
import vobject



correction_time = 978310800;
    
def calc_birthday(time):
    sec_2001 = float(time);
    sec_1970 = sec_2001+correction_time;

    date = datetime.date.fromtimestamp(sec_1970)

    return date


def typeid2str(id):
    if id == 1 | id == 11:
        return 'Iphone'
    if id == 3:
        return 'Festnetz'
    if id == 2:
        return 'Mobil'
    if id == 4:
        return 'Arbeit'
    return ''

sys.stdout = codecs.getwriter("UTF-8")(sys.stdout)

conn = sqlite3.connect('AddressBook.sqlitedb')
conn.row_factory = sqlite3.Row

f = open('contacs.vcf', 'w')

cContact = conn.cursor();
cContact.execute("SELECT * FROM ABPerson ORDER BY Last,First")


for contact in cContact:
    last = contact['Last'] if contact['Last'] != None else ''
    first = contact['First'] if contact['First'] != None else ''
     
    v = vobject.vCard()
     
    v.add('n')
    v.n.value = vobject.vcard.Name( family=last, given=first )
    v.add('fn')
    v.fn.value = first + ' ' + last
     
    if contact['Birthday'] != None:
        birthday = calc_birthday(contact['Birthday'])
        v.add('bday')
        v.bday.value = str(birthday.year) + '-' + str(birthday.month) + '-' + str(birthday.day)
            
    
    cEmail = conn.cursor()
    cEmail.execute("SELECT value,label FROM ABMultiValue WHERE record_id=? AND property=4 ORDER BY label", (contact["ROWID"],))

    for p in cEmail:
         if p['value'].find('@') > 2:
             e = v.add('email');
             e.value = p['value']


    # get phone numbers
    cPhone = conn.cursor();
    cPhone.execute("SELECT value,label FROM ABMultiValue WHERE record_id=? AND property=3 ORDER BY label", (contact["ROWID"],))
    for p in cPhone:
        t = v.add('tel')
        t.value = p['value']
        t.type_param = typeid2str(p['label'])
         


    # get addresse
    cAddress = conn.cursor();
    cAddress.execute("SELECT UID,value,label FROM ABMultiValue WHERE record_id=? AND property=5 ORDER BY label", (contact["ROWID"],))
    for p in cAddress:
        
        cValues = conn.cursor()
        cValues.execute("SELECT key,value FROM ABMultiValueEntry WHERE parent_id=? ORDER BY key", (p["UID"],))
        addr = {0:'', 1:'', 2:'', 3:'', 4:'', 5:''}
        for vs in cValues:
            addr[vs["key"]] = vs["value"]

        a = v.add('adr')
        a.value = vobject.vcard.Address(street=addr[1], code=addr[2], city=addr[3], country=addr[5])



    f.write(v.serialize())

f.close()
