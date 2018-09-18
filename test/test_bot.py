import starterbot

clean = starterbot.cleaning("Hello   WOrld!!  ")


def test_clean():
    assert clean == 'hello world'
