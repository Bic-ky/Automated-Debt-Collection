from import_export import resources
from .models import Bill
 
class BillResource(resources.ModelResource):
    class meta:
        model = Bill