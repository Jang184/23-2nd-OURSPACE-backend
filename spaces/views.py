import boto3, uuid

from django.http      import JsonResponse
from django.views     import View
from django.db.models import Min, Q, Count
from django.db        import transaction

from spaces.models    import Space, District, Category, Image, Option, Facility
from orders.models    import Order, OrderStatus
from users.models import User
from users.utils import login_decorator
from my_settings import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
from ourspace.settings import AWS_STORAGE_BUCKET_NAME

class ProductsView(View):

    def get(self, request):
        district_id  = request.GET.get('district', None)
        category_id  = request.GET.get('category', None)
        man_count    = request.GET.get('count', None)
        date         = request.GET.get('date', None)
        facilities   = request.GET.getlist('facility', None)
        order        = request.GET.get('order', None)

        prefix = {
            "desc"  : "-day_price",
            "aesc"  : "day_price",
            "best"  : "-like" 
        }
        
        q = Q()

        if district_id:
            q &= Q(district_id = district_id)

        if category_id:
            q &= Q(category_id = category_id)

        if man_count:
            q &= Q(min_count__lte = man_count) & Q(max_count__gte = man_count)

        if date:
            q_exclude = Q(order__status_id=OrderStatus.Status.COMPLETED.value) & Q(order__date=date)
            q_exclude &= ((Q(order__option__option="all") | Q(count_option = 2)))
            q &= ~q_exclude
        
        spaces = Space.objects.prefetch_related("image_set").select_related('district')\
                      .annotate(day_price=Min('option__price'), count_option = Count('order', distinct=True))\
                      .filter(q).order_by(prefix.get(order, "-like"))

        if facilities:
            for facility in facilities:
                spaces = spaces.filter(Q(facility = facility))

        result = [{
                    "id"        : space.id,
                    "address"   : space.address,
                    "title"     : space.title,
                    "sub_title" : space.sub_title,
                    "district"  : space.district.name,
                    "price"     : space.day_price,
                    "max_count" : space.max_count,
                    "image"     : [image.image for image in space.image_set.all()],
                    "like"      : space.like
                } for space in spaces]
            
        return JsonResponse({'RESULT':result}, status=200)

class DistrictView(View):
    def get(self, request):
        result = [{
                    "id"        : district.id,
                    "name"      : district.name,
                    "lattitude" : district.lattitude,
                    "longitude" : district.longitude 
                } for district in District.objects.all()]

        return JsonResponse({'RESULT':result}, status=200)

class CategoryView(View):
    def get(self, request):
        result = [{
            "id"    : category.id, 
            "name"  : category.name,
            "image" : category.image
        } for category in Category.objects.all()]

        return JsonResponse({'RESULT':result}, status=200)

class HostView(View):
    @login_decorator
    def post(self, request):
        user       = request.user
        data       = request.POST
        min_count  = request.POST.get('min_count', 2)
        like       = request.POST.get('like', 0)
        images     = request.FILES.getlist('image')
        facilities = request.POST.getlist('facility')
        signs      = [{'key':str(uuid.uuid4()) + image.name, 'image' : image} for image in images]

        s3_client = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
        )

        try:
            with transaction.atomic():
                space = Space.objects.create(
                    user        = user,
                    category_id = data['category'],
                    district_id = data['district'],
                    title       = data['title'],
                    sub_title   = data['sub_title'],
                    min_count   = min_count,
                    max_count   = data['max_count'],
                    address     = data['address'],
                    like        = like
                )
                Image.objects.bulk_create([
                    Image(space=space, image='https://ourspace-js.s3.ap-northeast-2.amazonaws.com/static/image/' + sign['key'])
                    for sign in signs
                ])
                Option.objects.bulk_create([
                    Option(space=space, option="day", price=data['price_day']),
                    Option(space=space, option='night', price=data['price_night']),
                    Option(space=space, option='all', price=data['price_all'])
                ])
                [space.facility.add(Facility.objects.get(id=facility))for facility in facilities]
                
                for sign in signs: 
                    s3_client.upload_fileobj(
                        sign['image'],
                        AWS_STORAGE_BUCKET_NAME,
                        'static/image/'+sign['key'],
                        ExtraArgs = {
                            'ContentType': sign['image'].content_type
                        }
                    )
                return JsonResponse({'message':'success'}, status=200)
        except KeyError:
            return JsonResponse({'message':'Key_Error'}, status=400)

class FacilityView(View):
    def get(self, request):
        results = [{
            'id' : facility.id,
            'name' : facility.name,
            'image' : facility.image
        }for facility in Facility.objects.all()]
        
        return JsonResponse({'results':results}, status=200)

class ProductDetailView(View):
    def get(self, request, space_id):

        if not Space.objects.filter(id=space_id).exists():
            return JsonResponse({'message':'No_Space'}, status=404)

        space = Space.objects.get(id=space_id)

        results = [{
            'id'         : space.id,
            'category_id': space.category.id,
            'district_id': space.district.id,
            'image'      : [image.image for image in space.image_set.all()],
            'title'      : space.title,
            'sub_title'  : space.sub_title,
            'min_count'  : space.min_count,
            'max_count'  : space.max_count,
            'address'    : space.address,
            'like'       : space.like,
            'price'      : [[option.id, option.option, option.price ]for option in space.option_set.all()],
            'facility'   : [{
                'id'   : facility.id,
                'name' : facility.name,
                'image': facility.image
                }for facility in space.facility.all()]
        }]

        return JsonResponse({'results':results}, status=200)

class DateFilterView(View):
    def get(self, request, space_id):
        date   = request.GET.get('date')
        option = request.GET.get('option')

        if not Order.objects.filter(space_id=space_id, date=date, status_id=OrderStatus.Status.COMPLETED.value).exists():
            return JsonResponse({'message':'OK'}, status=200)

        if option == 'all' :
            return JsonResponse({'message':'DENIED'}, status=400)

        orders = Order.objects.filter(space_id=space_id, date=date, status_id=OrderStatus.Status.COMPLETED.value)

        if orders.filter(Q(option__option='all') | Q(option__option=option)).exists():
            return JsonResponse({'message':'DENIED'}, status=400)

        return JsonResponse({'message':'OK'}, status=200)

class FacilityView(View):
    def get(self, request):
        results = [{
            'id'   : facility.id,
            'name' : facility.name,
            'image': facility.image
        }for facility in Facility.objects.all()]

        return JsonResponse({'results':results}, status=200)
