a="0:1:5"
b="0:1:5:1:2"
c="0:1:1:2:3"

test_id=a.split(":")
length_id=len(test_id)
b_id=b.split(":")
c_id=c.split(":")

#slice b_id accoring to length of test_id
b_id=b_id[:length_id]
c_id=c_id[:length_id]



print(test_id==b_id)
print(test_id==c_id)
