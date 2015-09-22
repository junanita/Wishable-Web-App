from django import forms
from django.forms import ModelForm

from django.forms import Textarea
from django.contrib.auth.models import User
from django.utils import html

from models import *

from django.utils.translation import ugettext_lazy as _

class RegistrationForm(forms.Form):
  first_name = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class':'form-control', 'autofocus':'autofocus'}))
  last_name  = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class':'form-control'}))
  email      = forms.EmailField(max_length=254, widget=forms.TextInput(attrs={'class':'form-control'}))
  username   = forms.CharField(max_length = 20, widget=forms.TextInput(attrs={'class':'form-control'}))
  password1  = forms.CharField(max_length = 200, 
                               label='Password', 
                               required=True,
                               widget = forms.PasswordInput(attrs={'class':'form-control'}))
  password2  = forms.CharField(max_length = 200, 
                               label='Confirm password',  
                               required=True,
                               widget = forms.PasswordInput(attrs={'class':'form-control'}))

 
  # Customizes form validation for properties that apply to more
  # than one field.  Overrides the forms.Form.clean function.
  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(RegistrationForm, self).clean()

    # Confirms that the two password fields match
    password1 = cleaned_data.get('password1')
    password2 = cleaned_data.get('password2')
    if password1 and password2 and password1 != password2:
      raise forms.ValidationError("Passwords did not match.")

    # We must return the cleaned data we got from our parent.
    return cleaned_data

  # Customizes form validation for the username field.
  def clean_username(self):
    # Confirms that the username is not already present in the
    # User model database.
    username = self.cleaned_data.get('username')
    if User.objects.filter(username__exact=username):
        raise forms.ValidationError("Username is already taken.")

    # We must return the cleaned data we got from the cleaned_data
    # dictionary
    return username


class LinkEntryForm(forms.Form):
  product_link = forms.URLField(max_length=500, 
    widget=forms.TextInput(attrs={'class':'form-control', 'autofocus':'autofocus', 'placeholder': 'Enter a valid url'}))

  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(LinkEntryForm, self).clean()

    link = cleaned_data.get('product_link')
    try: 
      if len(link) < 1:
        raise forms.ValidationError("Please enter a valid url.")
      if link == "" or (("http://" not in link) and ("https://" not in link) and ("www" not in link)) or link == None or link == 'NoneType':
        raise forms.ValidationError("Please enter a valid url.")
      if Product.objects.filter(productUrl__exact=link):
          raise forms.ValidationError("This product is aready in the database. Try searching instead.")
    except:
      raise forms.ValidationError("Please enter a valid url.")


    # We must return the cleaned data we got from our parent.
    return cleaned_data


class WishlistItemLinkForm(forms.Form):
  url = forms.URLField(max_length=500, 
    widget=forms.TextInput(attrs={'class':'form-control', 'autofocus':'autofocus'}))
  image_src = forms.URLField(max_length=500,
    required=False,
    widget=forms.TextInput(attrs={'class':'form-control'}))
  company = forms.CharField(max_length=200,
    widget=forms.TextInput(attrs={'class':'form-control'}))
  product_name = forms.CharField(max_length=200, 
    required=False,
    widget=forms.TextInput(attrs={'class':'form-control'}))
  price = forms.CharField(max_length=20, 
    required=False,
    widget=forms.TextInput(attrs={'class':'form-control'}))
  product_type = forms.ChoiceField(
    choices=[(0,"all"),(1,"books"),(2,"clothes"),
             (3,"home"),(4,"electronics"),(5,"health"),
             (6,"beauty"),(7,"misc")],
    required=False,
    widget=forms.Select(attrs={'class': 'form-control'}))
  description = forms.CharField(max_length=1000,
    required=False,
    widget=forms.Textarea(attrs={'class':'form-control'}))

  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(WishlistItemLinkForm, self).clean()

    # We must return the cleaned data we got from our parent.
    return cleaned_data



class WishListForm(forms.ModelForm):
  class Meta:
    model = WishList
    exclude = ('date', 'owner',)
    widgets = {
    'description': Textarea(attrs={'cols': 35, 'rows': 5,
                            'placeholder':"Add description",
                            'class':'form-control'}),
    }
    # labels = {
    #   'text' : ('Add a post'),
    # }
    # widgets = {
    #   'bio' : forms.Textarea(attrs={'cols':80, 'rows':4}),
    # }

class NewProductForm(forms.ModelForm):
  class Meta:
    model = Product
    excludes = ('date')

  # clean_picture taken from course repo. only when editing form
  def clean_picture(self):
      picture = self.cleaned_data['picture']
      if not picture:
          return None
      if not picture.content_type or not picture.content_type.startswith('image'):
          raise forms.ValidationError('File type is not image')
      if picture.size > MAX_UPLOAD_SIZE:
          raise forms.ValidationError('File too big (max size is {0} bytes)'.format(MAX_UPLOAD_SIZE))
      return picture 

  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(NewProductForm, self).clean()

    # We must return the cleaned data we got from our parent.
    return cleaned_data

class WishListItemForm(forms.ModelForm):
  class Meta:
    model = WishListItem
    exclude = ("product", "wishlist",)
    widgets = {
      'description': Textarea(attrs={'cols': 35, 'rows': 5,
                            'placeholder':"Add description",
                            'class':'form-control'}),
      }
    labels = {
        'description': _('Notes'),
    }

class SearchForm(forms.Form):
  search = forms.CharField(max_length=250, 
    widget=forms.TextInput(attrs={'class':'form-control', 
                                  'autofocus':'autofocus', 
                                  'placeholder':'What are you looking for?'}))

  def clean(self):
    # Calls the parent (forms.Form) .clean function, 
    # gets a dictionary of cleaned data as a result
    cleaned_data = super(SearchForm, self).clean()

    if cleaned_data.get('search') is None:
      raise forms.ValidationError("Please enter a valid search query.")

    # Strips whitespace from beginning and end of search query
    query_items = (cleaned_data.get('search')).strip()
    
    if "<" in query_items or ">" in query_items or "/" in query_items or "\\" in query_items:
      raise forms.ValidationError("Please remove special characters from your search (eg: <, >, /, \).")
    if len(query_items) < 1:
      raise forms.ValidationError("Please enter a valid search query.")

    # We must return the cleaned data we got from our parent.
    cleaned_data['query_items'] = query_items

    return cleaned_data


class FollowForm(forms.ModelForm):
  class Meta:
    model = Profile
    exclude = ('user',
              'age', 
              'bio', 
              'prefCompanies', 
              'picture', 
              'email')

class PrefCompaniesForm(forms.ModelForm):
  class Meta:
    model = Profile
    exclude = ('user',
              'age', 
              'bio', 
              'following', 
              'picture', 
              'email')

class EditProfileForm(forms.ModelForm):
  class Meta:
    model = Profile
    exclude = ('user',
              'email',
              'following',
              'prefCompanies',)
    widgets = {
    'age': Textarea(attrs={'cols': 35, 'rows': 1,
                            'autofocus':'autofocus',
                            'placeholder':"Change age",
                            'class':'form-control'}),
    'bio': Textarea(attrs={'cols': 35, 'rows': 5,
                            'placeholder':"Describe yourself",
                            'class':'form-control'}),
    }

  # def clean_picture(self):
  #   # print "YES"
  #   picture = self.cleaned_data.get('picture')
  #   # print picture
  #   # print "NO"
  #   if not picture:
  #     return None
  #   if not picture.content_type or not picture.content_type.startswith('image'):
  #       raise forms.ValidationError('File type is not image')
  #   return picture 

  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(EditProfileForm, self).clean()

    # We must return the cleaned data we got from our parent.
    return cleaned_data




class EditWishlistForm(forms.ModelForm):
  class Meta:
    model = WishList
    exclude = ('owner',
              'date',
              )
    widgets = {
    'name': Textarea(attrs={'cols': 35, 'rows': 1,
                            'autofocus':'autofocus',
                            'placeholder':"Change WishList Name",
                            'class':'form-control'}),
    'description': Textarea(attrs={'cols': 35, 'rows': 5,
                            'placeholder':"Add Descriptions",
                            'class':'form-control'}),
    }
  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(EditWishlistForm, self).clean()

    # We must return the cleaned data we got from our parent.
    return cleaned_data


class FairyGodMotherForm(forms.ModelForm):
  class Meta:
    model = WishListItem
    exclude = ('product',
              'wishlist',
              'description',
              'date')

  def clean(self):
    # Calls our parent (forms.Form) .clean function, gets a dictionary
    # of cleaned data as a result
    cleaned_data = super(FairyGodMotherForm, self).clean()

    # We must return the cleaned data we got from our parent.
    return cleaned_data




class UserSearchForm(forms.Form):
  search = forms.CharField(max_length=250, 
    widget=forms.TextInput(attrs={'class':'form-control', 
                                  'autofocus':'autofocus', 
                                  'placeholder':'Search for users by first name, last name, or username'}))

  def clean(self):
    # Calls the parent (forms.Form) .clean function, 
    # gets a dictionary of cleaned data as a result
    cleaned_data = super(UserSearchForm, self).clean()

    if cleaned_data.get('search') is None:
      raise forms.ValidationError("Please enter a valid search query.")

    # Strips whitespace from beginning and end of search query
    query_items = (cleaned_data.get('search')).strip()
    
    if "<" in query_items or ">" in query_items or "/" in query_items or "\\" in query_items:
      raise forms.ValidationError("Please remove special characters from your search (eg: <, >, /, \).")
    if len(query_items) < 1:
      raise forms.ValidationError("Please enter a valid search query.")

    # We must return the cleaned data we got from our parent.
    cleaned_data['query_items'] = query_items

    return cleaned_data