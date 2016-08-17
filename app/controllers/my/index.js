/* global dcodeIO */
import Ember from 'ember';

const {bcrypt} = dcodeIO;

export default Ember.Controller.extend({
    _error: null,
    newPass: null,
    confirmPass: null,
    sessionAccount: Ember.inject.service(),
    account: Ember.computed.alias('sessionAccount.account'),
    toast: Ember.inject.service(),

    passMatch: function() {
        this.set('_error');
        return this.get('newPass') === this.get('confirmPass');
    }.property('newPass', 'confirmPass'),

    canUpdate: Ember.computed.and('newPass', 'confirmPass', 'passMatch'),

    actions: {
        save() {
            this.get('account').save().then(() => {
                this.toast.info('Account updated successfully.');
            });
        },
        cancel() {
            this.get('account').rollbackAttributes();
        },
        updatePassword() {
            this.set('account.password', bcrypt.hashSync(this.get('newPass'), 10).replace('$2a$', '$2b$'));
            this.get('account').save().then(() => {
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
