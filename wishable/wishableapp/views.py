from django.shortcuts import render, redirect, get_object_or_404, render_to_response, RequestContext
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.http import HttpResponseRedirect

from django.template import Context

# Allows templates to be filled in and passed back as a string
from django.template.loader import render_to_string

# Decorator to use built-in authentication system
from django.contrib.auth.decorators import login_required

# Used to create and manually log in a user
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate

# Used to generate a one-time-use token to verify a user's email address
from django.contrib.auth.tokens import default_token_generator

# Used to send mail from within Django
from django.core.mail import send_mail

# Django transaction system so we can use @transaction.atomic
from django.db import transaction

# Functions for concatenating and sorting QuerySets for follower stream
from itertools import chain
from operator import attrgetter


from wishableapp.models import *
from wishableapp.forms import *
from wishableapp.webscraping import *
from wishableapp.searchdb import *

import re
import json

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

import urllib2
from urlparse import urlparse

from itertools import chain

''' 
Note to self: the urls in the render function call 
are template urls so they start from your template folder
'''

def home(request):
  return render(request, 'home.html')

@transaction.atomic
def register(request):
  context = {}

  # Just display the registration form if this is a GET request.
  if request.method == 'GET':
    context['form'] = RegistrationForm()
    return render(request, 'register.html', context)

  # Creates a bound form from the request POST parameters and makes the 
  # form available in the request context dictionary.
  form = RegistrationForm(request.POST)
  context['form'] = form

  # Validates the form.
  if not form.is_valid():
    return render(request, 'register.html', context)

  # At this point, the form data is valid.  Register and login the user.
  new_user = User.objects.create_user(username=form.cleaned_data['username'], 
                                      password=form.cleaned_data['password1'],
                                      first_name=form.cleaned_data['first_name'],
                                      last_name=form.cleaned_data['last_name'], 
                                      email=form.cleaned_data['email'])
  # Mark the user as inactive to prevent login before email confirmation.
  new_user.is_active = False
  new_user.save()

  new_profile = Profile(user=new_user)
  new_profile.save()

  # Generate a one-time use token and an email message body
  token = default_token_generator.make_token(new_user)

  email_body = """
  Welcome to Wishable! Please click the link below to
  verify your email address and complete the registration of your account:

  http://%s%s """ % (request.get_host(), 
                     reverse('confirm', args=(new_user.username, token)))

  send_mail(subject="Verify your email address",
            message= email_body,
            from_email="wishableapp@gmail.com",
            recipient_list=[new_user.email])


  context['email'] = form.cleaned_data['email']
  return render(request, 'needs-confirmation.html', context)

@transaction.atomic
def confirm_registration(request, username, token):
  user = get_object_or_404(User, username=username)
  if user == Http404:
    raise Http404("User does not exist.")

  # Send 404 error if token is invalid
  if not default_token_generator.check_token(user, token):
    raise Http404("You user token is invalid.")

  # Otherwise token was valid, activate the user.
  user.is_active = True
  user.save()
  return render(request, 'confirmed.html')



@login_required
@transaction.atomic
def wishing_well(request):
  context = {}
  if request.user:
    # get User
    user = get_object_or_404(User, username=request.user)
    userProfile = Profile.objects.get(user = user)
    context['userOperateProfile'] = userProfile
    # add yourself into your followees
    userProfile.following.add(userProfile)
    myfollowees = userProfile.following.all()
    myfolloweesWithoutMe = myfollowees.exclude(user=userProfile)
    # print myfollowees
    # followeesProfile = Profile.objects.filter(user = myfollowees)
    # followeesProducts = Product.objects.filter(user = myfollowees)
    context['followees'] = myfollowees
    # context['products'] = followeesProducts

    followeesWishlists = WishList.objects.filter(owner=myfollowees)
    # exclude other people's private wishlist
    followeesWishlistsWithoutOtherPrivate = followeesWishlists.exclude(owner=myfolloweesWithoutMe, private=True)

    # print followeesWishlists
    followeesWishlistItems = WishListItem.objects.filter(wishlist=followeesWishlistsWithoutOtherPrivate).order_by("-date")
    # print followeesWishlistItems

    context['wishListItems']=followeesWishlistItems


    if request.method == "GET":
      context['search_form'] = UserSearchForm()
      return render(request, 'wishing-well.html', context)

    else:
      # Create a bound form from the request POST parameters
      search_form = UserSearchForm(request.POST)

      # This does validation of the form
      if not search_form.is_valid():
        print "search form not valid"
        return HttpResponse("error")
        # return render(request, 'wishing-well.html', context)

      # The form is valid
      query_items = search_form.cleaned_data['query_items']

      # Produce a query object based on the search input
      user_query = get_query(query_items, ['username', 'first_name', 'last_name',])

      # Use the generated search query to search the database
      # Filter by popularity
      combined_results = User.objects.filter(user_query).order_by('last_name')
      print combined_results

      context['searchResults'] = combined_results

      # return render(request, 'foundUser.html', context)
      return_form = render_to_string('foundUser.html', context)
      return HttpResponse(return_form)

  else:
    context['user'] = 'No users here...'
  return render(request, 'wishing-well.html', context)



@login_required
def profile(request, username):
  # request.user is the user who do this operation
  # username is the user was asked to be viewed
  context = {}
  userViewed = "" 
  url = request.META.get('HTTP_REFERER')

  if request.user:   
    # Get user
    user = get_object_or_404(User, username = username)
    userProfile = Profile.objects.get(user=user)
    userOperate = get_object_or_404(User, username = request.user.username)
    userOperateProfile = Profile.objects.get(user=request.user)
    followees = userOperateProfile.following.all()
    if userProfile in followees:
      # print "True"
      context['isFollowed'] = True
    else:
      # print "False"
      context['isFollowed'] = False

    context['userWantFollow'] = user.username
    context['userWantUnfollow'] = user.username
    context['userOperate'] = request.user
    context['userProfile'] = userProfile
    context['user'] = user
    # context['followees'] = followees

    # Get user posts order by date.
    profile = Profile.objects.get(user = user)
    wishlists = WishList.objects.filter(owner=profile).order_by("-date")
    context['wishlists'] = wishlists

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
      if 'wishListID' in request.GET:
        print "YES"
      context['form'] = WishListForm()
      context['page'] = "profile"
      context['editProfileForm'] = EditProfileForm(instance=userProfile)
      context['editWishlistForm'] = EditWishlistForm()
      # print "YES"
      # print request.user
      # print url
      return render(request, 'profile.html', context)

    # Creates a bound form from the request POST parameters and makes the 
    # form available in the request context dictionary.
    form = WishListForm(request.POST)
    context['form'] = form
    # Validates the form.
    if not form.is_valid():
      return redirect(url)

    # At this point, the form data is valid.  Register and login the user.
    new_wishlist = WishList(name=form.cleaned_data['name'], 
                                owner=request.user.profile,
                                private=form.cleaned_data['private'],
                                description=form.cleaned_data['description'])

    new_wishlist.save()
    
    return redirect(url)

  else:
    context = {'user': "No users here..."}
  return redirect(url)


@login_required
@transaction.atomic
def editProfile(request, username):
  context ={} 
  url = request.META.get('HTTP_REFERER')

  if request.user:   
    # Get user
    userOperate = get_object_or_404(User, username = request.user.username)
    updateProfile = Profile.objects.get(user = userOperate)

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
      context['editProfileForm'] = EditProfileForm(instance=updateProfile)
      return render(request, 'profile.html', context)

    # Let user edit their Profile
    editProfileForm = EditProfileForm(request.POST or None, request.FILES, instance=updateProfile)
    context['editProfileForm'] = editProfileForm
    # print request.FILES
    # print editProfileForm
    if not editProfileForm.is_valid():
      print editProfileForm.errors
      # return render(request, "profile.html", context)
      return redirect(url)
    editProfileForm.save()
    return redirect(url)
  
  else:
    context = {'user': "No users here..."}
  return redirect(url)


@login_required
@transaction.atomic
def editWishList(request, wishListId):
  context ={} 
  url = request.META.get('HTTP_REFERER')

  if request.user:   
    # Get user
    userOperate = get_object_or_404(User, username = request.user.username)

    # Just display the registration form if this is a GET request.
    if request.method == 'GET':
      context['editProfileForm'] = EditWishlistForm()
      return render(request, 'profile.html', context)

    # Let user edit their Profile
    updateProfile = WishList.objects.get(id = wishListId)
    editWishlistForm = EditWishlistForm(request.POST, request.FILES, instance=updateProfile)
    context['editWishlistForm'] = editWishlistForm
    # print request.FILES
    # print editProfileForm
    if not editWishlistForm.is_valid():
      print editWishlistForm.errors
      return render(request, "profile.html", context)
    editWishlistForm.save()
    return redirect(url)
  
  else:
    context = {'user': "No users here..."}
  return redirect(url)


@login_required
@transaction.atomic
def catalog(request, prodtype="all"):
  context = {}
  if request.user:
    if request.method == "GET":
      context['user'] = request.user
      userProfile = Profile.objects.get(user=request.user)
      context['userProfile'] = userProfile
      context['userPrefCompanies'] = userProfile.prefCompanies.all()
      context['link_form'] = LinkEntryForm()
      context['search_form'] = SearchForm()

      # Get items
      if(prodtype == "all"):
        cItems = Product.objects.order_by("-popularity")
        # print cItems
      else:
        cItems = Product.objects.filter(product_type=prodtype).order_by("-popularity")
      context['cItems'] = cItems


      # Get user wishlists
      wishlists = WishList.objects.filter(owner=request.user.profile)
      context['wishlists'] = wishlists
      context['request'] = request
      return render(request, 'catalog.html', context)

    else:
      # Create a bound form from the request POST parameters
      search_form = SearchForm(request.POST)

      # This does validation of the form
      if not search_form.is_valid():

        if(prodtype == "all"):
          cItems = Product.objects.order_by("-popularity")
          # print cItems
        else:
          cItems = Product.objects.filter(product_type=prodtype).order_by("-popularity")

        context = {
          'user': request.user, 
          'link_form': LinkEntryForm(),
          'search_form': search_form,
          'cItems': cItems,
          'wishlist': wishlist,
        }
        userProfile = Profile.objects.get(user=request.user)
        context['userProfile'] = userProfile
        context['userPrefCompanies'] = userProfile.prefCompanies.all()
        return render(request, 'catalog.html', context)

      # The form is valid
      query_items = search_form.cleaned_data['query_items']

      # Produce a query object based on the search input
      product_query = get_query(query_items, ['name',])

      # Use the generated search query to search the database
      # Filter by popularity
      combined_results = Product.objects.filter(product_query).order_by('-popularity')

      context = {
        'user': request.user, 
        'link_form': LinkEntryForm(),
        'search_form': search_form,
        'cItems': combined_results,
        'wishlist': wishlist,
      }
      userProfile = Profile.objects.get(user=request.user)
      context['userProfile'] = userProfile
      context['userPrefCompanies'] = userProfile.prefCompanies.all()
      return render(request, 'catalog.html', context)

  else:
    context = {'user': "No users here..."}
  return render(request, 'catalog.html', context)

@login_required
def get_photo(request, id):
    profile = get_object_or_404(Profile, id=id)
    # userProfile = Profile.objects.get(user=user)
    if not profile.picture:
        raise Http404

    return HttpResponse(profile.picture)

@login_required
def get_product_photo(request, id):
    product = get_object_or_404(Product, id=id)
    if not product.picture:
        return Http404

    return HttpResponse(product.picture)

@login_required
def scrape_product(request):
  context={}
  if request.user:
    context['user'] = request.user  

    if request.method == "POST":

        # POST Request
        link_form = LinkEntryForm(request.POST)

        # Validate the form
        if not link_form.is_valid():
          context['link_form'] = link_form
          return_form = render_to_string('newproduct.html', context)
          return HttpResponse(return_form)

        new_link_form = LinkEntryForm()
        context['link_form'] = new_link_form

        url = link_form.cleaned_data['product_link']
        company = getCompany(url)

        # if the company is not in database
        if company is None:
           data = {
            'url': url,
            'company': "",
            'image_src': "",
            'product_name': "",
            'price': "", 
            'description': "",
          }
        # Modified Amazon API results
        elif company.name == "Amazon":
          product = getAmazonItemInfo(url) # a dictionary
          if product.get('errors') == None:
            data = {
              'url': url,
              'company': company.name,
              'image_src': product['imageURL'],
              'product_name': product['name'], 
              'price': product['price'], 
              'description': product['description']
            }
          else:
            data = {
              'url': url,
              'company': company.name,
              'image_src': "",
              'product_name': "", 
              'price': "", 
              'description': ""
            }
            context['errors'] = "Unable to collect data for this product. Please enter it manually."
        else:
          name = getProductName(url, company)
          price = getProductPrice(url, company)
          desc = getProductDesc(url, company)
          image_src = getProductImage(url, company)

          data = {
            'url': url,
            'company': company.name,
            'image_src': image_src,
            'product_name': name, 
            'price': price, 
            'description': desc
          }

        formatprice = re.findall("\d+.\d+", str(data['price']))
        data['price'] = formatprice[0] if formatprice else ''
        context['item_form'] = WishlistItemLinkForm(data)
        context['image_src'] = data['image_src']

        return_form = render_to_string('newproduct.html', context)
        return HttpResponse(return_form)
  else:
    context = {'user' : "No users here..."}
  return HttpResponseRedirect("catalog/all")

@login_required
def add_new_product(request):
  context = {}
  if request.user:
    context['user'] = request.user

    if request.method == "POST":

      # Get data from ajax call
      data = json.loads(request.POST.get("data"))
      types = ["all", "books" , "clothes", "home", "electronics", "health", "beauty", "misc"]

      company = Company.objects.get(name=data['company'])
      prod_data = {
        'user': request.user.id,
        'productUrl': data['url'],
        'name': data['product_name'], 
        'price': data['price'], 
        'description': data['description'],
        'product_type': types[int(data['product_type'])],
        'popularity' : 0,
        'available': True,
        'company': company.id
      }


      # Create new object.
      new_prod_form = NewProductForm(prod_data)


      if not new_prod_form.is_valid() and not new_prod_form.cleaned_data['picture'] :
        print "form not valid here"
        print new_prod_form.errors
        return HttpResponse(new_prod_form.errors.as_json())

      # print "form is fine"

      newprod = new_prod_form.save()

      # Get picture from line
      if data['image_src'] != "": 
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(urllib2.urlopen(data['image_src']).read())
        img_temp.flush()

        filename = urlparse(data['image_src']).path.split('/')[-1]

        newprod.picture.save(filename, File(img_temp))

      return HttpResponse("success")

  else:
    context = {'user' : "No users here..."}
  return render(request, 'catalog.html', context)


@login_required
@transaction.atomic
def add_to_wishlist(request):
  context = {}
  if request.user:
    context['user'] = request.user

    if request.method == "POST":

      prod_id = request.POST.get("productId")
      wishlist_id = request.POST.get("wishlistId")

      theproduct = Product.objects.get(id=prod_id)
      thewishlist = WishList.objects.get(id=wishlist_id)

      #Check to see if duplicate wishlistitem already exists.
      try:
        existing = WishListItem.objects.get(product=theproduct, wishlist=thewishlist)
        # fails here, item exists already
        context = {'errors' : {'This item is already added to your wishlist!'}}
        return HttpResponse('This item is already added to your wishlist!')
      except WishListItem.DoesNotExist:
        wishlistitem = WishListItem(product=theproduct, description=theproduct.description, wishlist=thewishlist)

      wishlistitem.save()

      newpopularity = theproduct.popularity + 1
      theproduct.popularity = newpopularity
      theproduct.save()

      return HttpResponse("success")

  else:
    context = {'user': "No users here..."}
  return HttpResponseRedirect("catalog/all")

@login_required
def wishlist(request, wishlist_id):
  context = {}
  if request.user:
    
    # get user
    # userOperate = get_object_or_404(User, username=request.user)
    user = get_object_or_404(User, username=request.user)

    context['user'] = user
    # context['userOperate'] = user
    context['userProfile'] = Profile.objects.get(user=user)

    try:
      wishlist = WishList.objects.get(id=wishlist_id)
      wishlistItems = WishListItem.objects.filter(wishlist=wishlist)
      requestProfile = Profile.objects.get(user=request.user)
      requestUserWishlists = WishList.objects.filter(owner=requestProfile)

      context['wishlist'] = wishlist
      context['wishlistItems'] = wishlistItems
      context['requestUserWishlists'] = requestUserWishlists

      return render(request, "wishlist.html", context)

    except ObjectDoesNotExist:
      context['errors'] = ['Wishlist does not exist']
      return render(request, "wishlist.html", context)

  else:
    context = {'user' : "No users here..."}
  return render(request, 'wishlist.html', context)

@login_required
@transaction.atomic
def delete_wishlist_item(request):
  context = {}
  if request.user:
    context['user'] = request.user

  try: 
    if request.method == "POST":
      # print("in post")
      wItemId = request.POST.get("wItemId")
      # print wItemId
      wishlistItem = WishListItem.objects.get(id=wItemId)
      wishlistItem.delete()
      return HttpResponse(wItemId)

  except ObjectDoesNotExist:
    context['errors'] = ["Wishlist Item doesn't exist. Can't delete. "]

  return HttpResponse()

@login_required
@transaction.atomic
def delete_wishlist(request):
  context = {}
  if request.user:
    context['user'] = request.user

  try: 
    if request.method == "POST":
      print("in post")
      wId = request.POST.get("wId")
      wishlist = WishList.objects.get(id=wId)
      wishlist.delete()
      return HttpResponse(wId)

  except ObjectDoesNotExist:
    context['errors'] = ["Wishlist Item doesn't exist. Can't delete. "]

  return HttpResponse()

@login_required
@transaction.atomic
def follow(request, username):
  context = {}
  url = "/" + 'profile' + "/" + str(username)

  if request.user:
    # print request.user
    # context = {'user': request.user}      
    if request.method =='POST':
      userOperate = get_object_or_404(User, username=request.user)
      userUpdate = Profile.objects.get(user = userOperate)
      userWantFollow = get_object_or_404(User, username=username)
      userFollowProfile = Profile.objects.get(user=userWantFollow)

      followForm = FollowForm(request.POST, instance=userUpdate)
      if not followForm.is_valid():
        return redirect(url)
      followForm.save()
      userUpdate.following.add(userFollowProfile)
      context['followForm'] = followForm
      
    else:
      followForm = FollowForm()
      context['followForm'] = followForm
  else:
       context['user'] = 'No users here...'
  return redirect(url)


@login_required
@transaction.atomic
def unfollow(request, username):
  context = {}
  # get current url 
  url = request.META.get('HTTP_REFERER')
  if request.user:
    # print request.user
    # context = {'user': request.user}
    if request.method =='POST':
      userOperate = get_object_or_404(User, username=request.user)
      userUpdate = Profile.objects.get(user=userOperate)
      userWantUnfollow = get_object_or_404(User, username=username)
      userUnfollowProfile = Profile.objects.get(user=userWantUnfollow)
     
      userUpdate.following.remove(userUnfollowProfile)
      followForm = FollowForm(request.POST, instance=userUpdate)
      if not followForm.is_valid():
        return redirect(url)
      followForm.save()
      context['followForm'] = followForm
  else:
    context['user'] = 'No users here...'
  return redirect(url)


@login_required
@transaction.atomic
def wishlist_item(request, wId):
  context = {}
  url = request.META.get('HTTP_REFERER')

  if request.user:
    wlItem = get_object_or_404(WishListItem, id=wId)

    # Produce a query object based on the search input
    product_query = get_query(wlItem.product.name, ['name','description',])

    # Use the generated search query to search the database
    # Filter by popularity
    combined_results = Product.objects.filter(product_query).exclude(id=wlItem.product.id).order_by('-popularity')
    all_productsA = Product.objects.all().exclude(id=wlItem.product.id).order_by('-popularity')
   
    profUser = Profile.objects.get(user=request.user)
    prefcomp = profUser.prefCompanies.all()

    all_products =  all_productsA.filter(company__in=prefcomp)
    combined_results_count = combined_results.count()

    #Get first 5
    if combined_results_count >= 4:
      four_results = combined_results[:4]
    elif all_products.count() >= 4:
      diff = 4 - combined_results_count
      rest_results = all_products[:diff]
      rel_results = combined_results[:combined_results_count]
      four_results = list(chain(rel_results, rest_results))
    else:
      four_results = combined_results

    context['four_results'] = four_results

    if request.method == "GET":
      context['wlItem'] = wlItem
      context['wItem'] = wlItem.product
      form = WishListItemForm(instance=wlItem)
      context['form'] = form
      return render(request, 'wishlist-item-page.html', context)

    form = WishListItemForm(request.POST or None, instance=wlItem)

    if not form.is_valid():
      return redirect(url)

    form.save()

    wishlistItems = WishListItem.objects.filter(wishlist=wlItem.wishlist)
    requestUserWishlists = WishList.objects.filter(owner=request.user.profile)

    context['form'] = form
    context['wishlist'] = wlItem.wishlist
    context['wishlistItems'] = wishlistItems
    context['requestUserWishlists'] = requestUserWishlists

    # Success
    return render(request, 'wishlist.html', context)

  else:
    context = {'user': "No users here..."}
  return redirect(url)

@login_required
def product(request, pId):
  context = {}
  url = request.META.get('HTTP_REFERER')

  if request.user:

    # get user
    user = get_object_or_404(User, username=request.user)
    context['user'] = user
    # context['userOperate'] = user
    context['userProfile'] = Profile.objects.get(user=user)

    # get product
    prod = get_object_or_404(Product, id=pId)
    # Produce a query object based on the search input
    product_query = get_query(prod.name, ['name','description',])

    # Use the generated search query to search the database
    # Filter by popularity
    combined_results = Product.objects.filter(product_query).exclude(id=prod.id).order_by('-popularity')
    all_products = Product.objects.all().exclude(id=prod.id).order_by('-popularity')
    combined_results_count = combined_results.count()

    #Get first 5
    if combined_results_count >= 4:
      four_results = combined_results[:4]
    elif all_products.count() >= 4:
      diff = 4 - combined_results_count
      rest_results = all_products[:diff]
      rel_results = combined_results[:combined_results_count]
      four_results = list(chain(rel_results, rest_results))
    else:
      four_results = combined_results

    context['four_results'] = four_results

    # Get wishlists of user
    profile = Profile.objects.get(user = request.user)
    wishlists = WishList.objects.filter(owner=profile).order_by("-date")
    # print wishlists
    context['wishlists'] = wishlists

    if request.method == "GET":
      context['pItem'] = prod
      # form = WishListItemForm(instance=wlItem)
      # context['form'] = form
      return render(request, 'product-page.html', context)

    # Success
    return render(request, 'product-page.html', context)

  else:
    context = {'user': "No users here..."}
  return redirect(url)

@login_required
@transaction.atomic
def addPrefCompanies(request, companyID):
  context={}
  url = request.META.get('HTTP_REFERER')
  if request.user:
    if request.method == "POST":
      user = get_object_or_404(User, username=request.user)
      userProfileUpdate = Profile.objects.get(user=user)
      addCompany = Company.objects.get(id=companyID)
      # form = PrefCompaniesForm(request.POST or None, instance=userProfileUpdate)
      # if not form.is_valid():
      #   return redirect(url)
      # form.save()
      # print type(userProfileUpdate.prefCompanies)
      userProfileUpdate.prefCompanies.add(addCompany)
      # print userProfileUpdate.prefCompanies.all()
  return redirect(url)


@login_required
@transaction.atomic
def removePrefCompanies(request, companyID):
  context={}
  url = request.META.get('HTTP_REFERER')
  if request.user:
    if request.method == "POST":
      user = get_object_or_404(User, username=request.user)
      userProfileUpdate = Profile.objects.get(user=user)
      addCompany = Company.objects.get(id=companyID)
      userProfileUpdate.prefCompanies.remove(addCompany)
      # form = PrefCompaniesForm(request.POST or None, instance=userProfileUpdate)
      # if not form.is_valid():
      #   return redirect(url)
      # form.save()
  return redirect(url)

@login_required
@transaction.atomic
def fairyGodMother(request, wItemId):
  context={}
  url = request.META.get('HTTP_REFERER')
  if request.user:
    if request.method == "POST":
      user = get_object_or_404(User, username=request.user)
      wishListItemUpdate = WishListItem.objects.get(id=wItemId)
      form = FairyGodMotherForm(request.POST or None, instance=wishListItemUpdate)
      if not form.is_valid():
        return redirect(url)
      form.save()
      wishListItemUpdate.fairyGodMother.add(user)
  return redirect(url)
