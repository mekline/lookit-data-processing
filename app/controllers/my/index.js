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

    _updateAccount() {
        return this.get('model').save()
            .then(() => this.toast.info('Account updated successfully.'))
            .catch(()=> this.toast.error('Could not update account details at this time; please try again later.'));
    },

    actions: {
        save() {
            const model = this.get('model');
            // IF and ONLY if email address field is dirty, also update sendgrid email suppressions.
            const isEmailDirty = !!model.changedAttributes().email;

            if (!isEmailDirty) {
                this._updateAccount();
            } else {
                // Get suppressions (old), then update account, then set suppressions for the new email address
                // If the first or third promises fail, make sure a toast error is shown correctly, b/c user will need
                //   to reset manually.
                let suppressions;
                model.getSuppressions()
                    .then(oldEmailSettings => suppressions = oldEmailSettings)
                    .then(() => this._updateAccount())
                    .then(() => {
                        const suppressionsHash = {};
                        // Construct suppressions hash; see notes on setSuppressions
                        (suppressions || [])
                            .forEach(item => suppressionsHash[item.id] = !item.subscribed);

                        return model.setSuppressions(suppressionsHash);
                    })
                    .catch(() => this.toast.error('Could not update notification preferences for your new email address. Please review the email preferences page.',
                        'Error while updating account'));
            }
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
