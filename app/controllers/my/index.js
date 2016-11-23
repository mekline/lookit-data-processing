/* global dcodeIO */
import Ember from 'ember';

const { bcrypt } = dcodeIO;

export default Ember.Controller.extend({
    toast: Ember.inject.service(),

    _error: null,
    newPass: null,
    confirmPass: null,

    passMatch: Ember.computed('newPass', 'confirmPass', function() {
        this.set('_error');
        return this.get('newPass') === this.get('confirmPass');
    }),

    canUpdate: Ember.computed.and('newPass', 'confirmPass', 'passMatch'),

    actions: {
        save() {
            this.get('model').save().then(() => {
                this.toast.info('Account updated successfully.');
            });
        },
        cancel() {
            this.get('model').rollbackAttributes();
        },
        updatePassword() {
            this.set('model.password', bcrypt.hashSync(this.get('newPass'), 10).replace('$2a$', '$2b$'));
            this.get('model').save().then(() => {
                this.set('_error', null);
                this.set('newPass', null);
                this.set('confirmPass', null);
                this.toast.info('Password updated successfully.');
            }, () => {
                this.set('_error', 'Could not update password');
            });
        }
    }
});
