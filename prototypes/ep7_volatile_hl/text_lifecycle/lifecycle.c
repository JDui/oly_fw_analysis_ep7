#include "lifecycle.h"
int ep7_text_create_attach(struct ep7_text_lifecycle *s,
 const struct ep7_text_lifecycle_ops *o, void *owner,
 const void *descriptor, const uint16_t *text, int qualified)
{
 void *child;
 if (!s || !o || !qualified || !owner || !descriptor || !text ||
     s->child || s->owner || s->bound || !o->create || !o->initialized ||
     !o->destroy_unattached || !o->attach || !o->bind_parent || !o->set_text)
  return EP7_TEXT_CREATE_REJECTED;
 child=o->create(o->context,owner,descriptor);
 if (!child) return EP7_TEXT_CREATE_REJECTED;
 if (o->initialized(o->context,child)!=1) {
  o->destroy_unattached(o->context,child);
  return EP7_TEXT_CREATE_REJECTED;
 }
 if (o->attach(o->context,owner,child)!=1) {
  o->destroy_unattached(o->context,child);
  return EP7_TEXT_CREATE_REJECTED;
 }
 /* Even binding/render failure cannot return child to unattached ownership. */
 s->child=child; s->owner=owner;
 if (o->bind_parent(o->context,child,owner)!=1)
  return EP7_TEXT_ATTACHED_DISPLAY_FAILED;
 s->bound=1;
 if (o->set_text(o->context,child,text)!=1)
  return EP7_TEXT_ATTACHED_DISPLAY_FAILED;
 return EP7_TEXT_ATTACHED_READY;
}
void ep7_text_revoke(struct ep7_text_lifecycle *s)
{
 if (s) { s->child=NULL; s->owner=NULL; s->bound=0; }
}
