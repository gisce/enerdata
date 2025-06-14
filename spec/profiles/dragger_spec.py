# -*- coding: utf-8 -*-
from enerdata.profiles.profile import *
from expects import *
from mamba import description, it, context


with description('A dragger object'):
    with it('must return the integer of the number'):
        d = Dragger()
        aprox = d.drag(32.453)
        expect(aprox).to(equal(32))

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
        expect(aprox).to(equal(1))
        expect(d['key1']).to(equal(Decimal('0')))

        aprox = d.drag(5.2, key='key2')
        expect(aprox).to(equal(6))
        expect(d['key2']).to(equal(Decimal('-0.5')))

    with context('Has to use the drag of antecesor drag'):
        with context('If the current drag is >= 0.5'):
            with it('has to return number + 1 and drag will be < 0'):
                d = Dragger()
                aprox = d.drag(32.453)
                aprox2 = d.drag(1.1)
                expect(aprox2).to(equal(2))
                expect(d['default']).to(be_below_or_equal(0))

        with context('If the curren drag is < 0.5'):
            with it('has to return number'):
                d = Dragger()
                aprox = d.drag(32.453)
                aprox2 = d.drag(1.046)
                expect(aprox2).to(equal(1))

        with context('if receives 0.5 and 0'):
            with it('has to drag -0.5 and return 1 and 0'):
                d = Dragger()
                approx = d.drag(0.5)
                dragging = d['default']
                expect(approx).to(equal(1))
                expect(dragging).to(equal(Decimal('-0.5')))
                aprox = d.drag(0)
                dragging = d['default']
                expect(aprox).to(equal(0.0))
                expect(dragging).to(equal(Decimal('-0.5')))
        with context('Curve in W to kW'):
            with it('Must be the same total +/- 1 kW'):
                import json
                with open('spec/fixtures/curves/curve.json', 'r') as fj:
                    orig_W = json.load(fj)
                #orig_W = [0, 0, 0, 0, 208, 292, 292, 208]
                total_W = sum(orig_W)
                curve_kW = []
                d = Dragger()
                for value in orig_W:
                    curve_kW.append(d.drag(round(value / 1000.0, 3)))
                total_kW = sum(curve_kW)
                diff = abs((total_kW * 1000) - total_W)
                expect(diff).to(be_below_or_equal(1000))
