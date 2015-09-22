from django.db import models

# User class for built-in authentication module
from django.contrib.auth.models import User

# Natural Keys: Foreign Keys in Fixtures
class HtmlElemManager(models.Manager):
  def get_by_natural_key(self, _tag, _id, _class, _customAttr, _customVal):
    return self.get(_tag = _tag, _id = _id, _class = _class, _customAttr = _customAttr, _customVal = _customVal)

# Storing all company's html elements
class HtmlElem(models.Model):
  objects = HtmlElemManager()

  _tag  = models.CharField(max_length=20, blank = True)
  _id  = models.CharField(max_length=160, blank = True)
  _class  = models.CharField(max_length=160, blank = True)
  _customAttr = models.CharField(max_length=160, blank = True)
  _customVal = models.CharField(max_length=160, blank = True)


  class Meta:
    unique_together = (('_tag', '_id', '_class', '_customAttr', '_customVal'),)
  def _unicode_(self):
    return "name: " + str(self._tag) + " id: " + str(self._id) + " class: " + str(self._class) + " customAttr: " + str(self._customAttr) + " customVal: " + str(self._customVal)


class Company(models.Model):
  name          = models.CharField(max_length=200, blank = True)
  favicon       = models.FileField(upload_to="favicons", blank = True)
  baseUrl       = models.URLField(blank = True)
  nameAttrTag  = models.OneToOneField(HtmlElem, related_name = "name", blank = True, null=True)
  priceAttrTag  = models.OneToOneField(HtmlElem, related_name = "price", blank = True, null=True)
  descAttrTag  = models.OneToOneField(HtmlElem, related_name = "description", blank = True, null=True)
  imageAttrTag = models.OneToOneField(HtmlElem, related_name = "image", blank = True, null=True)
  date          = models.DateTimeField(auto_now_add=True, blank = True, null=True)
  def _unicode_(self):
    return "name: " + str(self.name) + " id: " + str(self._id) 

class Product(models.Model):
  user         = models.ForeignKey(User, blank = True, null=True)
  isbn13       = models.CharField(max_length=13, blank = True)
  company      = models.ForeignKey(Company, blank = True, null=True, related_name="products")
  product_type = models.CharField(max_length=20)
  picture      = models.FileField(upload_to="pictures", blank = True)
  productUrl   = models.URLField(max_length=1000)
  price        = models.DecimalField(max_digits=8, decimal_places=2)
  name         = models.CharField(max_length=160)
  description  = models.TextField(max_length=2000)
  popularity   = models.IntegerField(default=0)
  available    = models.BooleanField(default=True)
  date         = models.DateTimeField(auto_now_add=True, blank=True, null=True)
  def _unicode_(self):
    return "name: " + str(self.name) + " id: " + str(self._id) 


class Profile(models.Model):
  user          = models.OneToOneField(User)
  age           = models.IntegerField(blank=True, null=True)
  bio           = models.CharField(blank=True, max_length=430, null=True)
  following     = models.ManyToManyField('self', symmetrical=False, blank=True, null=True)
  prefCompanies = models.ManyToManyField(Company, symmetrical=False, blank=True, null=True)
  picture       = models.FileField(upload_to="pictures", blank=True, null=True)
  email         = models.CharField(max_length=100, blank=True, null=True)
  def __unicode__(self):
    return str(self.user.first_name) + " " + str(self.user.last_name) + " " + '('+str(self.user.username)+')'

class WishList(models.Model):
  name          = models.CharField(max_length=200, default="New_Wishlist", blank=True, null=True)
  owner         = models.ForeignKey(Profile)
  private       = models.BooleanField(default=False)
  description   = models.CharField(max_length=200, blank=True, null=True)
  date          = models.DateTimeField(auto_now_add=True)
  def _unicode_(self):
    return "name: " + str(self.name) + " id: " + str(self._id) 

class WishListItem(models.Model):
  product        = models.ForeignKey(Product)
  wishlist       = models.ForeignKey(WishList)
  fairyGodMother = models.ManyToManyField(User, null=True, blank=True)
  description    = models.CharField(max_length=200)
  date         = models.DateTimeField(auto_now_add=True, blank=True, null=True)
  def _unicode_(self):
    return self.product.name
