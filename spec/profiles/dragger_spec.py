from decimal import Decimal

from enerdata.profiles.profile import *
from expects import *

with description('A dragger object'):
    with it('must return the integer of the number'):
        d = Dragger()
        aprox = d.drag(32.453)
        expect(aprox).to(be(32))

    with it('must keep the decimal part'):
        d = Dragger()
        aprox = d.drag(32.453)
        expect(Decimal(d['default'])).to(equal(Decimal('0.453')))

    with it('has to save the decimal part to default key if is not set'):
        d = Dragger()
        aprox = d.drag(1.01)
        expect(d).to(have_key('default'))

    with it('has to work with diferent keys independently'):
        d = Dragger()
        aprox = d.drag(1.6, key='key1')
        aprox2 = d.drag(2.3, key='key2')
        expect(d['key1']).to(equal(Decimal('-0.4')))
        expect(d['key2']).to(equal(Decimal('0.3')))

        aprox = d.drag(1.4, key='key1')
        expect(aprox).to(be(1))
        expect(d['key1']).to(equal(Decimal('0')))

        aprox = d.drag(5.2, key='key2')
        expect(aprox).to(be(6))
        expect(d['key2']).to(equal(Decimal('-0.5')))


    with context('Has to use the drag of antecesor drag'):

        with context('If the current drag is >= 0.5'):
            with it('has to return number + 1 and drag will be < 0'):
                d = Dragger()
                aprox = d.drag(32.453)
                aprox2 = d.drag(1.1)
                expect(aprox2).to(be(2))
                expect(d['default']).to(be_below_or_equal(0))

        with context('If the curren drag is < 0.5'):
            with it('has to return number'):
                d = Dragger()
                aprox = d.drag(32.453)
                aprox2 = d.drag(1.046)
                expect(aprox2).to(be(1))
