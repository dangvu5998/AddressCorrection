# Sửa địa chỉ 
Sửa lại địa chỉ định dạng ...xã/thị trấn...quận/huyện/tp...tỉnh/tp...
Địa chỉ đầu vào chỉ chứa kí tự và dấu cách (không chứa dấu phẩy). API sẽ tự sửa lỗi và thêm dấu phẩy
```
from src.address_correction import AddressCorrection
address_correction = AddressCorrection()
address_correction.address_correction('thọ nghip xuân trương nam dịnh')
# return ('thọ nghiệp, xuân trường, nam định', 1.6)

